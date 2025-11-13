import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from llm_client import create_llm_client


def _normalize_model_id(name: str) -> str:
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


def _ensure_report_exists(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find research report at {path}. "
            "Run agent_researcher.py first or provide --input."
        )
    return path.read_text(encoding="utf-8")


def _extract_json_payload(raw: str) -> str:
    if not raw:
        return raw
    stripped = raw.strip()
    if stripped.startswith('```'):
        stripped = re.sub(r'^```(?:json)?', '', stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r'```$', '', stripped).strip()
    match = re.search(r'\{[\s\S]*\}', stripped)
    if match:
        return match.group(0).strip()
    return stripped



_ALLOWED_CODEPOINT_RANGES = (
    (0x0009, 0x000A),
    (0x000D, 0x000D),
    (0x0020, 0x007E),
    (0x1100, 0x11FF),
    (0x3130, 0x318F),
    (0xA960, 0xA97F),
    (0xAC00, 0xD7A3),
    (0xD7B0, 0xD7FF),
)


def _is_allowed_char(ch: str) -> bool:
    code = ord(ch)
    for lower, upper in _ALLOWED_CODEPOINT_RANGES:
        if lower <= code <= upper:
            return True
    return False


def _sanitize_string(text: str) -> str:
    return "".join(ch for ch in text if _is_allowed_char(ch))


def _sanitize_structure(value):  # type: ignore[no-untyped-def]
    if isinstance(value, str):
        return _sanitize_string(value)
    if isinstance(value, dict):
        return {key: _sanitize_structure(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_sanitize_structure(item) for item in value]
    return value


def _save_markdown(payload: dict, markdown_path: Path) -> None:
    lines: list[str] = []
    company = payload.get("company", "")
    job_role = payload.get("job_role", "")
    job_level = payload.get("job_level", "")

    if company or job_role:
        lines.append(f"# {company} {job_level} {job_role} 테이크홈 과제")
        lines.append("")

    for assignment in payload.get("assignments", []):
        title = assignment.get("title", "과제")
        lines.append(f"## {title}")
        if assignment.get("mission"):
            lines.append(assignment["mission"])
            lines.append("")
        sections = (
            ("요약", "summary"),
            ("핵심 요구사항", "requirements"),
            ("제출물", "deliverables"),
            ("AI 활용 가이드라인", "ai_guidelines"),
            ("평가 기준", "evaluation"),
            ("예상 소요 시간", "timeline"),
            ("심층 토론 질문", "discussion_questions"),
        )
        for header, key in sections:
            value = assignment.get(key)
            if not value:
                continue
            lines.append(f"### {header}")
            if isinstance(value, list):
                for item in value:
                    lines.append(f"- {item}")
            else:
                lines.append(str(value))
            lines.append("")
    markdown_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def run_question_generator(
    job_role: str,
    job_level: str = "Senior",
    company_name: str = "Myrealtrip OTA Company",
    input_path: str = "research_report.txt",
    output_path: str = "assignments.json",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    language: str = "Korean",
    markdown_preview_path: Optional[str] = None,
) -> str:
    load_dotenv()

    print(f"--- Generating assignments for: {job_role} ({job_level}) ---")

    report_path = Path(input_path)
    research_summary = _ensure_report_exists(report_path)

    temp_val = temperature if temperature is not None else float(os.getenv("OPENAI_TEMPERATURE", "0.35"))
    llm = create_llm_client(model=model, temperature=temp_val)

    schema_description = json.dumps(
        {
            "type": "object",
            "required": ["company", "job_role", "job_level", "assignments"],
            "properties": {
                "company": {"type": "string"},
                "job_role": {"type": "string"},
                "job_level": {"type": "string"},
                "assignments": {
                    "type": "array",
                    "minItems": 5,
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "required": [
                            "id",
                            "title",
                            "mission",
                            "requirements",
                            "deliverables",
                            "ai_guidelines",
                            "evaluation",
                            "timeline",
                            "discussion_questions",
                            "datasets",
                            "starter_code",
                        ],
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "mission": {"type": "string"},
                            "summary": {"type": "string"},
                            "requirements": {"type": "array", "items": {"type": "string"}},
                            "deliverables": {"type": "array", "items": {"type": "string"}},
                            "ai_guidelines": {"type": "array", "items": {"type": "string"}},
                            "evaluation": {"type": "array", "items": {"type": "string"}},
                            "timeline": {"type": "string"},
                            "discussion_questions": {
                                "type": "array",
                                "minItems": 3,
                                "maxItems": 5,
                                "items": {"type": "string"},
                            },
                            "datasets": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "format", "records", "columns"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "format": {"type": "string", "enum": ["csv", "json"]},
                                        "records": {"type": "integer", "minimum": 10, "maximum": 2000},
                                        "filename": {"type": "string"},
                                        "columns": {
                                            "type": "array",
                                            "minItems": 2,
                                            "maxItems": 8,
                                            "items": {
                                                "type": "object",
                                                "required": ["name"],
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "type": {
                                                        "type": "string",
                                                        "enum": [
                                                            "string",
                                                            "text",
                                                            "integer",
                                                            "float",
                                                            "boolean",
                                                            "date",
                                                            "datetime",
                                                            "category",
                                                        ],
                                                        "default": "string",
                                                    },
                                                    "description": {"type": "string"},
                                                    "choices": {
                                                        "type": "array",
                                                        "items": {"type": "string"},
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                            "starter_code": {
                                "type": "object",
                                "properties": {
                                    "language": {"type": "string"},
                                    "description": {"type": "string"},
                                    "filename": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
        ensure_ascii=False,
        indent=2,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """당신은 OTA 산업 전문 채용 디렉터입니다. 모든 결과는 JSON 형식으로 반환하며, 한국어와 영문 기술 용어만 사용하고 한자·중국어 문자를 절대 포함하지 않습니다.""",
            ),
            (
                "user",
                """회사명: {company_name}
직무: {job_level} {job_role}
언어: {language}

연구 요약:
{research_summary}

위 정보를 참고하여 OTA 서비스 맥락에 맞는 테이크홈 과제 5개를 설계하세요.
- 각 과제는 서로 다른 Myrealtrip 고객 여정 또는 OTA 기능 영역을 다루고, 중복되지 않는 문제를 제시해야 합니다.
- 모든 assignment에는 최소 1개의 맞춤형 데이터셋(`datasets`)과 스타터 코드 메타데이터(`starter_code`)를 포함시키고, 내용이 과제 요구사항과 긴밀히 연결되도록 하세요.
- 데이터셋의 `description`과 `columns`는 과제에서 다루는 문제를 해결하는 데 필요한 정보를 전달해야 하며, `records` 값은 10~2000 범위에서 현실적인 크기를 설정하세요.
- `starter_code`에는 후보자가 바로 활용할 수 있도록 언어(`language`), 파일명(`filename`), 제공 목적을 명확히 설명하고 과제 맥락과 연결하세요.
- 모든 설명은 간결하면서도 실무 지침이 되도록 작성하며, 기술 용어(예: API, Swift, Compose)는 영어를 유지할 수 있으나 그 외에는 한글을 사용하세요.

JSON Schema:
{schema_description}
""",
            ),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    raw_json = chain.invoke(
        {
            "company_name": company_name,
            "job_role": job_role,
            "job_level": job_level,
            "language": language,
            "research_summary": research_summary,
            "schema_description": schema_description,
        }
    )

    cleaned_json = _extract_json_payload(raw_json)

    try:
        parsed = json.loads(cleaned_json)
    except json.JSONDecodeError as exc:
        debug_path = Path(output_path).with_suffix(".raw.json")
        debug_path.write_text(raw_json, encoding="utf-8")
        cleaned_path = Path(output_path).with_suffix(".cleaned.json")
        cleaned_path.write_text(cleaned_json, encoding="utf-8")
        raise ValueError(
            "Failed to parse assignments JSON. Raw output saved to "
            f"{debug_path} (raw) and {cleaned_path} (cleaned)."
        ) from exc

    sanitized = _sanitize_structure(parsed)
    sanitized["company"] = company_name
    sanitized["job_role"] = job_role
    sanitized["job_level"] = job_level

    output_file = Path(output_path)
    output_file.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"--- Assignments JSON saved to: {output_file} ---")

    if markdown_preview_path:
        _save_markdown(sanitized, Path(markdown_preview_path))
    else:
        preview_path = output_file.with_suffix(".md")
        _save_markdown(sanitized, preview_path)
        print(f"--- Preview markdown saved to: {preview_path} ---")

    return str(output_file)


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate structured take-home assignments from research report",
    )
    parser.add_argument("job_role", nargs="+", help="Role to tailor assignments for")
    parser.add_argument("--level", default="Senior", help="Job level calibration")
    parser.add_argument("--company", default="Myrealtrip OTA Company", help="Company/brand name")
    parser.add_argument("--input", default="research_report.txt", help="Path to research report input")
    parser.add_argument("--output", default="assignments.json", help="Path to write structured assignments JSON")
    parser.add_argument("--markdown", help="Optional markdown preview path")
    parser.add_argument("--model", help="Override model (e.g., deepseek/deepseek-chat-v3.1)")
    parser.add_argument("--temperature", type=float, help="Temperature override (default 0.35)")
    parser.add_argument("--language", default="Korean", help="Output language (default Korean)")
    parser.add_argument("--env-file", help="Extra .env file to load")
    parser.add_argument("--profile", help="Profile name to load .env.<profile>")
    return parser.parse_args(argv)


def _load_profiles(args: argparse.Namespace) -> None:
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
    _load_profiles(cli_args)

    role = " ".join(cli_args.job_role).strip()
    if not role:
        print("Error: job_role cannot be empty", file=sys.stderr)
        sys.exit(1)

    run_question_generator(
        job_role=role,
        job_level=cli_args.level,
        company_name=cli_args.company,
        input_path=cli_args.input,
        output_path=cli_args.output,
        model=cli_args.model,
        temperature=cli_args.temperature,
        language=cli_args.language,
        markdown_preview_path=cli_args.markdown,
    )
