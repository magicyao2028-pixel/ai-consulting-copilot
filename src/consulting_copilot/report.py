from __future__ import annotations

from typing import Any


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Evidence-Backed Decision Memo",
        "",
        f"**Question:** {result['decision_question']}",
        f"**Status:** {result['status']}",
        f"**Confidence:** {result['confidence']}",
        "",
        "## Executive decision",
        "",
        result["executive_decision"],
    ]
    _claim_section(lines, "Findings", result.get("findings", []))
    _claim_section(lines, "Options", result.get("options", []))
    _claim_section(lines, "Recommendations", result.get("recommendations", []))
    _claim_section(lines, "Risks", result.get("risks", []))

    if result.get("pilot_plan"):
        lines.extend(["", "## 30-day pilot plan", ""])
        lines.extend(f"- **Days {item['days']}:** {item['action']}" for item in result["pilot_plan"])
    if result.get("missing_evidence"):
        lines.extend(["", "## Missing evidence", ""])
        lines.extend(f"- {item}" for item in result["missing_evidence"])

    coverage = result["citation_coverage"]
    lines.extend([
        "",
        "## Evidence controls",
        "",
        f"- Citation coverage: {coverage['cited_claims']}/{coverage['total_claims']} "
        f"({coverage['percentage']}%)",
        f"- Ignored unverified evidence: {', '.join(result.get('ignored_unverified_evidence', [])) or 'none'}",
        "- Human approval required: yes",
        "",
        "## Evidence register",
        "",
    ])
    for item in result["evidence_register"]:
        lines.append(
            f"- **[{item['evidence_id']}] {item['title']}** — {item['claim']} "
            f"({item['source_type']}, {item['reliability']}, {item['collected_at']})"
        )
    lines.extend(["", "_Public demonstration data is synthetic. This memo is not a production outcome claim._", ""])
    return "\n".join(lines)


def _claim_section(lines: list[str], title: str, claims: list[dict[str, Any]]) -> None:
    if not claims:
        return
    lines.extend(["", f"## {title}", ""])
    for item in claims:
        citations = " ".join(f"[{evidence_id}]" for evidence_id in item["evidence_ids"])
        lines.append(f"- {item['claim']} {citations}")
