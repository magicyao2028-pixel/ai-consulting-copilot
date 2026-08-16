from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import load_engagement, load_scenarios
from .scenarios import compare_scenarios


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare governed AI-pilot threshold scenarios.")
    parser.add_argument("engagement", type=Path, help="Structured engagement JSON")
    parser.add_argument("scenarios", type=Path, help="JSON list with at least two declared scenarios")
    parser.add_argument("--output", type=Path, default=Path("output/scenario_comparison.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = compare_scenarios(load_engagement(args.engagement), load_scenarios(args.scenarios))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scenario comparison written to {args.output}")


if __name__ == "__main__":
    main()
