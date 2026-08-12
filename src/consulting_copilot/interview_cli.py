from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .interviews import load_json_object, normalize_interview_notes, review_candidate_claims


def write_json(payload: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_main() -> None:
    parser = argparse.ArgumentParser(description="Normalize synthetic interview notes into review candidates.")
    parser.add_argument("notes", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/interview_candidates.json"))
    args = parser.parse_args()
    result = normalize_interview_notes(load_json_object(args.notes))
    write_json(result, args.output)
    print(f"Candidate claims written to {args.output}; no evidence was promoted automatically")


def review_main() -> None:
    parser = argparse.ArgumentParser(description="Record human decisions and export approved interview evidence.")
    parser.add_argument("normalization", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/interview_review.json"))
    args = parser.parse_args()
    result = review_candidate_claims(load_json_object(args.normalization), load_json_object(args.review))
    write_json(result, args.output)
    print(f"Human review result written to {args.output}")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"normalize", "review"}:
        raise SystemExit("usage: python -m consulting_copilot.interview_cli {normalize|review} ...")
    command = sys.argv.pop(1)
    normalize_main() if command == "normalize" else review_main()


if __name__ == "__main__":
    main()
