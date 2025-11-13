import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

from llm_client import create_llm_client


def _normalize_model_id(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    return name


def _openrouter_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {}
    site = os.getenv("OPENROUTER_SITE_URL")
    app = os.getenv("OPENROUTER_APP_NAME")
    if site:
        headers["HTTP-Referer"] = site
    if app:
        headers["X-Title"] = app
    return headers


def _read_html(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {path}")
    return path.read_text(encoding="utf-8")


def _extract_json(text: str) -> dict:
    blocks = re.findall(r"```\s*json\s*([\s\S]+?)```", text, flags=re.IGNORECASE)
    candidates: List[str] = []
    if blocks:
        candidates.append(blocks[-1])
    candidates.append(text)

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Failed to parse JSON from designer output")


def _recent_google_search(query: str) -> str:
    import requests

    key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_ID")
    if not key or not cx:
        return "Google API key / CSE ID missing."

    months = 3
    match = re.search(r"months:(\d+)", query)
    if match:
        months = max(1, min(int(match.group(1)), 12))
        query = re.sub(r"months:\d+", "", query)

    params = {
        "q": query.strip() or "take home assignment web design",
        "key": key,
        "cx": cx,
        "num": 6,
        "dateRestrict": f"m{months}",
    }
    try:
        resp = requests.get("https://customsearch.googleapis.com/customsearch/v1", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        lines = []
        for item in items:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            lines.append(f"- {title}\n  {link}\n  {snippet}")
        return "\n".join(lines) or "No design references found."
    except Exception as exc:
        return f"Search error: {exc}"


def run_web_designer(
    html_path: str = "index.html",
    css_output: str = "styles.css",
    notes_output: str = "design_notes.md",
    language: str = "Korean",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Dict[str, str]:
    load_dotenv()

    html_content = _read_html(Path(html_path))

    temp_val = temperature if temperature is not None else float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    llm = create_llm_client(model=model, temperature=temp_val)

    design_research = _recent_google_search(
        "modern landing page design best practices 2024 typography accessibility"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "당신은 WCAG 2.1 AA 기준을 철저히 준수하는 시니어 UI/UX 아키텍트입니다. 지시된 JSON 스키마 외에는 어떠한 텍스트도 반환하지 마십시오.",
            ),
            (
                "user",
                """다음 HTML 구조를 분석하고 최신 디자인/접근성 인사이트를 반영한 디자인 시스템을 설계하십시오.

출력 형식(필수):
{{
  "css": "...",
  "design_summary": "...",
  "accessibility_notes": "...",
  "color_palette": ["#...", "#...", "#...", "#...", "#...", "#...", "#..."]
}}

지침:
- `css`는 섹션 주석(1. Google Fonts Import, 2. CSS Variables, 3. Base Styles & Reset, 4. Layout & Components, 5. Responsive Queries, 6. Dark Mode)을 포함합니다.
- Myrealtrip 브랜드 컬러(딥블루 #0F4C81, 청록 #1BA6A4, 포인트 오렌지 #FF7A59)를 기반으로 중립 톤과 상태 색상을 정의하세요.
- `.top-nav`, `.assignments-tabs`, `.assignment-panel`, `.guide-section`, `.apply-section` 등 핵심 BEM 클래스에 대한 상태(hover, focus, selected) 스타일을 명확히 규정하십시오.
- `design_summary`와 `accessibility_notes`는 {language}로 작성하고, 생성형 AI 활용 및 검증 프로세스에 대한 기대치를 언급합니다.
- 헤더 고정, 탭 포커스 이동, 라디오 기반 탭 전환의 접근성 패턴, CTA 버튼 강조 등 세부 사항을 포함하세요.
- HTML 구조 변경이나 추가 마크업 제안은 금지됩니다.

최신 디자인 리서치 요약:
{design_research}

분석 대상 HTML(발췌):
{html_excerpt}
""",
            ),
        ]
    )

    excerpt = html_content if len(html_content) <= 6000 else html_content[:6000]

    result = (prompt | llm).invoke(
        {
            "language": language,
            "design_research": design_research,
            "html_excerpt": excerpt,
        }
    )

    content = getattr(result, "content", str(result))
    parsed = _extract_json(content)

    css_text = parsed.get("css", "")
    if not css_text:
        raise ValueError("No CSS returned by design agent")

    Path(css_output).write_text(css_text.strip() + "\n", encoding="utf-8")

    notes_lines: List[str] = []
    if parsed.get("design_summary"):
        notes_lines.append("## Design Summary\n" + parsed["design_summary"].strip())
    if parsed.get("accessibility_notes"):
        notes_lines.append("\n## Accessibility Notes\n" + parsed["accessibility_notes"].strip())
    if parsed.get("color_palette"):
        palette = parsed["color_palette"]
        palette_str = "\n".join(f"- {hexcode}" for hexcode in palette)
        notes_lines.append("\n## Color Palette\n" + palette_str)

    if notes_output:
        Path(notes_output).write_text("\n\n".join(notes_lines).strip() + "\n", encoding="utf-8")

    print(f"--- CSS saved to {css_output} ---")
    if notes_output:
        print(f"--- Design notes saved to {notes_output} ---")

    return parsed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Design agent that styles the take-home assignment page")
    parser.add_argument("--html", default="index.html", help="Path to generated HTML page")
    parser.add_argument("--css", default="styles.css", help="Output CSS file path")
    parser.add_argument("--notes", default="design_notes.md", help="Where to store design rationale")
    parser.add_argument("--language", default="Korean", help="Language for textual output")
    parser.add_argument("--model", help="Override model name")
    parser.add_argument("--temperature", type=float, help="Temperature override")
    parser.add_argument("--env-file", help="Optional extra .env file")
    parser.add_argument("--profile", help="Profile name (.env.<profile>)")
    return parser.parse_args()


def _load_env_overrides(args: argparse.Namespace) -> None:
    load_dotenv()
    if args.env_file:
        load_dotenv(args.env_file, override=True)
    if args.profile:
        base_dir = Path(__file__).resolve().parent
        profile_path = base_dir / f".env.{args.profile}"
        if profile_path.exists():
            load_dotenv(profile_path, override=True)
        else:
            print(f"Warning: profile file not found: {profile_path}", file=sys.stderr)


if __name__ == "__main__":
    cli_args = _parse_args()
    _load_env_overrides(cli_args)

    run_web_designer(
        html_path=cli_args.html,
        css_output=cli_args.css,
        notes_output=cli_args.notes,
        language=cli_args.language,
        model=cli_args.model,
        temperature=cli_args.temperature,
    )
