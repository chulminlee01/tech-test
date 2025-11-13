import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, List
import re
import requests

from dotenv import load_dotenv
try:
    # Try new import path (LangChain 0.2+)
    from langchain.agents import AgentExecutor, create_react_agent
except ImportError:
    # Fallback to old import path
    from langchain_core.agents import AgentExecutor, create_react_agent

from langchain_core.tools import Tool
from langchain import hub

from llm_client import create_llm_client


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {var_name}. "
            f"Set it in your .env file."
        )
    return value


def _normalize_model_id(name: str) -> str:
    """Return the model identifier exactly as provided."""
    return name


def _openrouter_headers() -> Dict[str, str]:
    """Build optional headers recommended by OpenRouter.

    Reads OPENROUTER_SITE_URL and OPENROUTER_APP_NAME from env.
    Returns an empty dict if not set.
    """
    headers: Dict[str, str] = {}
    site = os.getenv("OPENROUTER_SITE_URL")
    app = os.getenv("OPENROUTER_APP_NAME")
    if site:
        headers["HTTP-Referer"] = site
    if app:
        headers["X-Title"] = app
    return headers

def _recent_months_default() -> int:
    try:
        return int(os.getenv("RECENT_MONTHS", "6"))
    except Exception:
        return 6


def _compose_topic(job_role: Optional[str], job_level: Optional[str]) -> str:
    today = datetime.now()
    role = (job_role or "Software Engineer").strip()
    level = (job_level or "Mid-level").strip()
    return (
        f"{today:%Y-%m} {level} {role} OTA take-home coding assignments: interview"
        " expectations, evaluation criteria, AI usage policies, and best practices"
    )

def recent_google_search(query: str) -> str:
    """Search Google CSE with a date restriction to recent months.

    Accepts optional inline tokens in the query:
    - months:N  -> limit to last N months (default from RECENT_MONTHS env, 6)
    - num:N     -> number of results (1-10, default 8)
    The rest of the text is treated as the search query.
    """
    key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_ID")
    if not key or not cx:
        return "Google API key / CSE ID missing. Set GOOGLE_API_KEY and GOOGLE_CSE_ID."
    
    print(f"🔍 Searching Google CSE: '{query[:80]}...'", flush=True)

    m = re.findall(r"(?:(months|num)\s*:\s*(\d+))", query)
    months = _recent_months_default()
    num = 8
    for k, v in m:
        if k == "months":
            months = max(1, min(12, int(v)))
        elif k == "num":
            num = max(1, min(10, int(v)))
    # Strip tokens from the query
    cleaned = re.sub(r"\b(months|num)\s*:\s*\d+\b", "", query).strip()
    if not cleaned:
        cleaned = query

    params = {
        "q": cleaned,
        "key": key,
        "cx": cx,
        "num": num,
        "dateRestrict": f"m{months}",  # last N months
    }
    try:
        resp = requests.get(
            "https://customsearch.googleapis.com/customsearch/v1",
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return f"Error during recent search: {exc}"

    raw_items = data.get("items", []) or []
    lines: List[str] = []
    for item in raw_items:
        try:
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")
            if not all(isinstance(val, str) and val.strip() for val in (title, link, snippet)):
                continue
            # Defensive filtering: skip rows that look like raw CSV/JSON dumps
            suspect_payload = any(x.strip().startswith("{") or x.strip().startswith("[") for x in (title, snippet))
            if suspect_payload:
                continue
            safe_title = title.replace("\n", " ").strip()
            safe_link = link.strip()
            safe_snippet = snippet.replace("\n", " ").strip()
            lines.append(f"- {safe_title}\n  {safe_link}\n  {safe_snippet}")
        except Exception:
            continue

    if not lines:
        print(f"   ⚠️  No results found", flush=True)
        return "No well-formed search results available in the requested window."

    result_text = "\n".join(lines[:num])
    print(f"   ✅ Found {len(lines)} results from Google CSE", flush=True)
    return result_text


def run_researcher(
    topic: Optional[str] = None,
    output_path: str = "research_report.txt",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    job_role: Optional[str] = None,
    job_level: Optional[str] = None,
) -> str:
    """Run a LangChain ReAct agent with Google Search and save findings.

    Args:
        topic: Optional explicit topic. If omitted, a topic is generated from
            the provided ``job_role`` and ``job_level``.
        output_path: Where to save the research report.
        model: Optional model override.
        temperature: Optional temperature override.
        job_role: Role used to shape automatic queries.
        job_level: Level used to shape automatic queries.

    Returns:
        The path to the written report file.
    """
    # Load env (idempotent). Caller may have already loaded specific .env files.
    load_dotenv()

    # Validate required environment variables early for clearer errors
    # Check for at least one LLM API key (NVIDIA or OpenRouter)
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not nvidia_key and not openrouter_key:
        raise RuntimeError(
            "Missing required LLM API key. Set either NVIDIA_API_KEY or OPENROUTER_API_KEY in your .env file.\n"
            "- NVIDIA: Get at https://build.nvidia.com/\n"
            "- OpenRouter: Get at https://openrouter.ai/"
        )
    _require_env("GOOGLE_API_KEY")
    _require_env("GOOGLE_CSE_ID")

    if not topic:
        topic = _compose_topic(job_role, job_level)

    print(f"--- Starting research on: {topic} ---")
    months_window = _recent_months_default()
    print(f"🔍 Research Tool: Google Custom Search Engine (last {months_window} months)")
    print(f"📡 Search Engine ID: {os.getenv('GOOGLE_CSE_ID')}")

    # Allow model override via args, then env; default to configured model with fallback
    temp_val = temperature if temperature is not None else float(os.getenv("OPENAI_TEMPERATURE", "0"))
    llm = create_llm_client(model=model, temperature=temp_val)

    # Prefer a recent Google search tool limited to last N months
    tools = [
        Tool(
            name="google_search_recent",
            func=recent_google_search,
            description=(
                "Search the web for sources from the last few months. "
                "Use inline tokens like 'months:3' or 'num:5' to adjust."
            ),
        )
    ]
    print(f"🤖 Agent initialized with Google CSE tool")

    # Pull a standard ReAct prompt from LangChain Hub
    prompt = hub.pull("hwchase17/react")

    agent = create_react_agent(llm, tools, prompt)
    max_iters = int(os.getenv("AGENT_MAX_ITERATIONS", "8"))
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,  # recover if the LLM mixes final answer + action
        max_iterations=max_iters,
        early_stopping_method="force",
    )

    # Encourage structured, source‑rich output
    today = datetime.now().strftime("%B %Y")
    role_label = (job_role or "Software Engineer").strip()
    level_label = (job_level or "Mid-level").strip()

    user_input = (
        f"You are analyzing the latest take-home coding assignment expectations for {level_label} {role_label} roles "
        f"in OTA travel companies (e.g., Myrealtrip, global OTA peers) as of {today}. Begin by proposing 3-5 targeted "
        f"google_search_recent queries that cover interview formats, evaluation criteria, AI usage policies, and "
        f"representative company examples. Execute those searches using google_search_recent (already restricted to the "
        f"past {months_window} months) and synthesize the findings into a concise report with bullet points, source URLs, "
        f"consensus, disagreements, and gaps in evidence."
    )

    response = agent_executor.invoke({"input": user_input})

    output_text = response.get("output") or response.get("final_output") or str(response)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    print(f"--- Research report saved to: {output_path} ---")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep Researcher: LangChain ReAct agent with Google Search (recent bias)")
    parser.add_argument("topic", nargs="*", help="Optional topic override (leave blank for auto-generated)")
    parser.add_argument("--output", default="research_report.txt", help="Output file path")
    parser.add_argument("--model", help="Override model name (e.g., gpt-4o, gpt-4o-mini)")
    parser.add_argument("--temperature", type=float, help="Sampling temperature override (e.g., 0, 0.2)")
    parser.add_argument("--env-file", help="Path to a .env file to load (overrides existing env)")
    parser.add_argument("--profile", help="Profile name to load .env.<profile> from this folder (overrides)")
    parser.add_argument("--recent-months", type=int, help="Default recency window in months for google_search_recent (default 6)")
    parser.add_argument("--job-role", help="Role context for auto topic generation")
    parser.add_argument("--job-level", help="Level context for auto topic generation")

    args = parser.parse_args()

    # Load default .env, then optional env-file, then optional profile (each overriding the previous)
    load_dotenv()
    if args.env_file:
        load_dotenv(args.env_file, override=True)

    if args.profile:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        profile_path = os.path.join(base_dir, f".env.{args.profile}")
        if os.path.exists(profile_path):
            load_dotenv(profile_path, override=True)
        else:
            print(f"Warning: profile file not found: {profile_path}", file=sys.stderr)

    # Set default recency window if provided
    if args.recent_months:
        os.environ["RECENT_MONTHS"] = str(max(1, min(12, int(args.recent_months))))

    topic = " ".join(args.topic).strip() or None
    run_researcher(
        topic,
        output_path=args.output,
        model=args.model,
        temperature=args.temperature,
        job_role=args.job_role,
        job_level=args.job_level,
    )
