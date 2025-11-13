import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from llm_client import create_llm_client


LANGUAGE_EXTENSION = {
    "kotlin": "kt",
    "swift": "swift",
    "python": "py",
    "typescript": "ts",
    "javascript": "js",
    "java": "java",
    "csharp": "cs",
    "go": "go",
    "dart": "dart",
    "ruby": "rb",
}


_ALLOWED_TEXT_PATTERN = re.compile(r"[\u0009\u000A\u000D\u0020-\u007E\u1100-\u11FF\u3130-\u318F\uA960-\uA97F\uAC00-\uD7FF]")


def _sanitize_text(value: str) -> str:
    return "".join(match.group(0) for match in _ALLOWED_TEXT_PATTERN.finditer(value))


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


def _load_assignments(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Assignments file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _dataset_preview(dataset: dict) -> Dict[str, object]:
    path = dataset.get("path")
    if not path:
        return {"available": False}
    file_path = Path(path)
    if not file_path.exists():
        return {"available": False}

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path, nrows=5)
        return {
            "available": True,
            "type": "csv",
            "columns": list(df.columns),
            "preview": df.to_dict(orient="records"),
        }

    if file_path.suffix.lower() == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            preview = data[:5]
        else:
            preview = [data]
        return {"available": True, "type": "json", "preview": preview}

    return {"available": False}


def _build_llm(model: Optional[str], temperature: Optional[float]):
    temp_val = temperature if temperature is not None else float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    return create_llm_client(model=model, temperature=temp_val)


def _parse_code_block(content: str) -> str:
    match = re.search(r"```[a-zA-Z0-9+]*\n([\s\S]+?)```", content)
    if match:
        return match.group(1).strip()
    return content.strip()


def run_starter_code_generator(
    assignments_path: str = "assignments.json",
    assignment_id: Optional[str] = None,
    output_dir: str = "starter_code",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    myrealtrip_url: str = "https://www.myrealtrip.com/",
) -> Dict[str, Path]:
    load_dotenv()

    payload = _load_assignments(Path(assignments_path))
    assignments = payload.get("assignments", [])

    selected = []
    if assignment_id:
        selected = [a for a in assignments if a.get("id") == assignment_id]
        if not selected:
            raise ValueError(f"Assignment id '{assignment_id}' not found in {assignments_path}")
    else:
        selected = assignments

    if not selected:
        print("--- No assignments available for starter code generation. ---")
        return {}

    llm = _build_llm(model, temperature)
    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    generated: Dict[str, Path] = {}

    for assignment in selected:
        info = assignment.get("starter_code") or {}
        language = (info.get("language") or "kotlin").lower()
        description = info.get("description") or "핵심 기능 뼈대를 제공하세요."
        extension = LANGUAGE_EXTENSION.get(language, "txt")
        assignment_id_value = assignment.get("id") or f"assignment_{len(generated)+1:02d}"
        default_filename = info.get("filename") or f"{assignment_id_value}_starter.{extension}"
        filename = Path(default_filename).name
        file_path = output_directory / filename

        dataset_briefs = []
        for dataset in assignment.get("datasets", []):
            dataset_briefs.append(
                {
                    "name": dataset.get("name"),
                    "description": dataset.get("description"),
                    "preview": _dataset_preview(dataset),
                }
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """당신은 Myrealtrip OTA Company의 시니어 엔지니어입니다. 후보자가 빠르게 시작할 수 있도록 간결한 스타터 코드를 제공합니다. 모든 주석과 설명은 한국어로 작성하되, 언어 문법은 해당 언어 규칙을 따릅니다. 코드 외의 한자나 중국어 문자는 사용하지 않습니다.""",
                ),
                (
                    "user",
                    """과제 정보:
ID: {assignment_id}
제목: {title}
미션: {mission}
요약: {summary}
주요 요구사항:
{requirements}

제공 데이터셋:
{datasets}

스타터 코드 요구사항:
{starter_description}

Myrealtrip 참고 URL: {myrealtrip_url}

지침:
1. {language} 파일 하나에 포함될 수 있는 최소 실행 또는 템플릿 코드를 작성하세요.
2. 데이터셋 미리보기를 참고해 모델/DTO/Mock 데이터 등을 정의하세요.
3. 네트워크 요청이 필요한 경우, Myrealtrip API가 없으므로 mocking 또는 placeholder 주석을 추가하세요.
4. 코드 외의 설명은 주석으로만 작성하고, 최종 출력은 단일 코드 블록으로 반환하세요.
""",
                ),
            ]
        )

        serialized_requirements = "\n".join(f"- {req}" for req in assignment.get("requirements", [])) or "- [정보 없음]"
        serialized_datasets = json.dumps(dataset_briefs, ensure_ascii=False, indent=2)

        chain = prompt | llm | StrOutputParser()
        raw_output = chain.invoke(
            {
                "assignment_id": assignment_id_value,
                "title": assignment.get("title"),
                "mission": assignment.get("mission"),
                "summary": assignment.get("summary") or "",
                "requirements": serialized_requirements,
                "datasets": serialized_datasets,
                "starter_description": description,
                "language": language,
                "myrealtrip_url": myrealtrip_url,
            }
        )

        code_content = _sanitize_text(_parse_code_block(raw_output))
        if not code_content:
            raise ValueError(f"Starter code generation failed for assignment {assignment_id_value}")

        file_path.write_text(code_content + "\n", encoding="utf-8")
        info["language"] = language
        info["filename"] = filename
        info["path"] = file_path.as_posix()
        info["download_href"] = _relative_path(file_path)
        generated[assignment_id_value] = file_path
        print(f"--- Starter code saved: {file_path}")

    assignments_path_obj = Path(assignments_path)
    assignments_path_obj.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return generated


def _relative_path(path: Path) -> str:
    root = Path.cwd()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return os.path.relpath(path, root).replace(os.sep, "/")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate starter code files for assignments")
    parser.add_argument("--input", default="assignments.json", help="Path to assignments JSON")
    parser.add_argument("--assignment-id", help="Generate starter code for a single assignment id")
    parser.add_argument("--output-dir", default="starter_code", help="Directory to write starter files")
    parser.add_argument("--model", help="Override model name")
    parser.add_argument("--temperature", type=float, help="Temperature override")
    parser.add_argument("--myrealtrip-url", default="https://www.myrealtrip.com/", help="Reference URL")
    parser.add_argument("--env-file", help="Extra .env file to load")
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
            print(f"Warning: profile file not found: {profile_path}")


if __name__ == "__main__":
    cli_args = _parse_args()
    _load_env_overrides(cli_args)

    run_starter_code_generator(
        assignments_path=cli_args.input,
        assignment_id=cli_args.assignment_id,
        output_dir=cli_args.output_dir,
        model=cli_args.model,
        temperature=cli_args.temperature,
        myrealtrip_url=cli_args.myrealtrip_url,
    )
