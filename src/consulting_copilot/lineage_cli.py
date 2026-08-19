from __future__ import annotations

import argparse
from pathlib import Path

from .copilot import ConsultingCopilot
from .lineage import build_evidence_lineage, write_lineage
from .models import load_engagement


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic evidence-lineage graph.")
    parser.add_argument("engagement", type=Path, nargs="?", default=Path("data/sample_engagement.json"))
    parser.add_argument("--json-output", type=Path, default=Path("examples/evidence_lineage.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("examples/evidence_lineage.md"))
    args = parser.parse_args()
    graph = build_evidence_lineage(ConsultingCopilot().analyze(load_engagement(args.engagement)))
    write_lineage(graph, args.json_output, args.markdown_output)
    print(f"Evidence lineage: {graph['summary']['claim_nodes']} cited claims")


if __name__ == "__main__":
    main()
