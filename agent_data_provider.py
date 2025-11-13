import argparse
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from faker import Faker


def _ensure_assignments(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Assignments JSON not found: {path}. Run agent_question_generator.py first or provide --input."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _sanitize_filename(stem: str, extension: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in stem.lower())
    safe = safe.strip("_") or "dataset"
    return f"{safe}.{extension}"


def _generate_value(fake: Faker, column: dict) -> object:
    col_type = (column.get("type") or "string").lower()
    choices = column.get("choices")
    if choices:
        return random.choice(choices)

    if col_type in {"string", "text"}:
        return fake.sentence(nb_words=8) if col_type == "text" else fake.word()
    if col_type == "integer":
        return random.randint(0, 1000)
    if col_type == "float":
        return round(random.uniform(0, 1000), 2)
    if col_type == "boolean":
        return random.choice([True, False])
    if col_type == "date":
        return fake.date_this_year().isoformat()
    if col_type == "datetime":
        return fake.date_time_this_year().isoformat()
    if col_type == "category":
        return fake.word()
    return fake.word()


def _relative_href(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return os.path.relpath(path, root).replace(os.sep, "/")


def _generate_dataset(fake: Faker, spec: dict, output_dir: Path, default_stem: str) -> Path:
    fmt = (spec.get("format") or "csv").lower()
    stem = spec.get("filename") or f"{default_stem}_{spec.get('name', 'dataset')}"
    filename = _sanitize_filename(Path(stem).stem, fmt)
    path = output_dir / filename

    records = max(10, min(int(spec.get("records", 200)), 5000))
    columns = spec.get("columns") or []
    if not columns:
        raise ValueError(f"Dataset '{spec.get('name')}' requires at least one column definition.")

    rows: List[Dict[str, object]] = []
    for _ in range(records):
        row = {}
        for col in columns:
            col_name = col.get("name")
            if not col_name:
                continue
            row[col_name] = _generate_value(fake, col)
        rows.append(row)

    if fmt == "json":
        path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)

    return path


def run_data_provider(
    assignments_path: str = "assignments.json",
    output_dir: str = "datasets",
    language: str = "Korean",
) -> List[Path]:
    load_dotenv()

    assignments_file = Path(assignments_path)
    payload = _ensure_assignments(assignments_file)
    assignments = payload.get("assignments", [])

    if not assignments:
        print("--- No assignments found; skipping dataset generation. ---")
        return []

    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    random.seed(42)
    fake = Faker(language)
    fake.seed_instance(42)

    generated_paths: List[Path] = []
    project_root = Path.cwd()

    for assignment in assignments:
        assignment_id = assignment.get("id") or f"assignment_{len(generated_paths)+1:02d}"
        datasets = assignment.get("datasets") or []
        if not datasets:
            continue
        for index, spec in enumerate(datasets, start=1):
            default_stem = f"{assignment_id}_{index:02d}"
            dataset_path = _generate_dataset(fake, spec, output_directory, default_stem)
            spec["filename"] = Path(dataset_path.name).as_posix()
            spec["path"] = dataset_path.as_posix()
            spec["download_href"] = _relative_href(dataset_path, project_root)
            generated_paths.append(dataset_path)
            print(f"--- Generated dataset for {assignment_id} -> {dataset_path}")

    assignments_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("--- Dataset generation complete and assignments JSON updated. ---")
    return generated_paths


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate datasets defined in assignments.json")
    parser.add_argument("--input", default="assignments.json", help="Path to structured assignments JSON")
    parser.add_argument("--output-dir", default="datasets", help="Directory to store generated datasets")
    parser.add_argument("--language", default="Korean", help="Language hint for faker (default Korean)")
    parser.add_argument("--env-file", help="Additional .env file to load")
    parser.add_argument("--profile", help="Profile name (loads .env.<profile>)")
    return parser.parse_args(argv)


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

    run_data_provider(
        assignments_path=cli_args.input,
        output_dir=cli_args.output_dir,
        language=cli_args.language,
    )
