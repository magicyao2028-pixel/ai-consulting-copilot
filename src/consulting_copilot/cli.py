from __future__ import annotations

import argparse
import json
from pathlib import Path

from .copilot import ConsultingCopilot
from .models import load_engagement
from .report import render_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an evidence-backed business decision memo.")
    parser.add_argument("engagement", type=Path, help="Structured engagement JSON")
    parser.add_argument("--json-output", type=Path, default=Path("output/decision_memo.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("output/decision_memo.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = ConsultingCopilot().analyze(load_engagement(args.engagement))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    print(f"Decision memo written to {args.json_output} and {args.markdown_output}")


if __name__ == "__main__":
    main()
