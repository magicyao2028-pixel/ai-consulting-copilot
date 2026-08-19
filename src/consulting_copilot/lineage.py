from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CLAIM_GROUPS = ("findings", "options", "recommendations", "risks")


def build_evidence_lineage(memo: dict[str, Any]) -> dict[str, Any]:
    register = memo.get("evidence_register")
    if not isinstance(register, list) or not register:
        raise ValueError("Decision memo must contain an evidence register")
    evidence_by_id: dict[str, dict[str, Any]] = {}
    nodes: list[dict[str, Any]] = []
    for item in register:
        evidence_id = str(item.get("evidence_id", "")).strip() if isinstance(item, dict) else ""
        if not evidence_id or evidence_id in evidence_by_id:
            raise ValueError("Evidence IDs must be present and unique")
        freshness = item.get("freshness")
        if not isinstance(freshness, dict) or not isinstance(freshness.get("eligible_for_decision"), bool):
            raise ValueError(f"Evidence {evidence_id} lacks decision-eligibility metadata")
        evidence_by_id[evidence_id] = item
        nodes.append({
            "node_id": evidence_id,
            "kind": "evidence",
            "reliability": item.get("reliability"),
            "freshness_status": freshness.get("freshness_status"),
            "eligible_for_decision": freshness["eligible_for_decision"],
        })

    edges: list[dict[str, str]] = []
    claim_nodes: list[dict[str, Any]] = []
    for group in CLAIM_GROUPS:
        claims = memo.get(group)
        if not isinstance(claims, list):
            raise ValueError(f"Decision memo {group} must be a list")
        for index, claim in enumerate(claims, start=1):
            claim_text = str(claim.get("claim", "")).strip() if isinstance(claim, dict) else ""
            evidence_ids = claim.get("evidence_ids") if isinstance(claim, dict) else None
            if not claim_text or not isinstance(evidence_ids, list) or not evidence_ids:
                raise ValueError(f"Every {group} claim must contain text and evidence IDs")
            if any(not isinstance(evidence_id, str) or not evidence_id.strip() for evidence_id in evidence_ids):
                raise ValueError(f"Every {group} citation must be a non-empty evidence ID")
            node_id = f"{group[:-1]}:{index:03d}"
            unsupported = sorted(set(evidence_ids).difference(evidence_by_id))
            if unsupported:
                raise ValueError(f"Unknown evidence citation in {node_id}: {', '.join(unsupported)}")
            ineligible = sorted(evidence_id for evidence_id in set(evidence_ids) if not evidence_by_id[evidence_id]["freshness"]["eligible_for_decision"])
            if ineligible:
                raise ValueError(f"Ineligible evidence cannot support {node_id}: {', '.join(ineligible)}")
            claim_nodes.append({"node_id": node_id, "kind": "claim", "group": group, "claim": claim_text})
            edges.extend({"from": evidence_id, "to": node_id, "relationship": "supports"} for evidence_id in sorted(set(evidence_ids)))

    decision_id = "decision:executive"
    nodes.extend(claim_nodes)
    nodes.append({"node_id": decision_id, "kind": "decision", "status": memo.get("status"), "human_approval_required": bool(memo.get("governance", {}).get("human_approval_required"))})
    recommendation_ids = [item["node_id"] for item in claim_nodes if item["group"] == "recommendations"]
    if not recommendation_ids:
        raise ValueError("Decision memo must contain at least one cited recommendation")
    edges.extend({"from": node_id, "to": decision_id, "relationship": "informs"} for node_id in recommendation_ids)
    excluded_lists = [
        memo.get("ignored_unverified_evidence", []),
        memo.get("stale_evidence", []),
        memo.get("future_dated_evidence", []),
    ]
    if any(not isinstance(items, list) for items in excluded_lists):
        raise ValueError("Excluded-evidence fields must be lists")
    excluded_values = [evidence_id for items in excluded_lists for evidence_id in items]
    if any(not isinstance(evidence_id, str) or not evidence_id.strip() for evidence_id in excluded_values):
        raise ValueError("Excluded-evidence entries must be non-empty evidence IDs")
    excluded = sorted(set(excluded_values))
    if set(excluded).difference(evidence_by_id):
        raise ValueError("Excluded-evidence lists reference unknown evidence IDs")
    return {
        "lineage_version": "0.5",
        "engagement_id": memo.get("engagement_id"),
        "nodes": nodes,
        "edges": edges,
        "excluded_evidence_ids": excluded,
        "summary": {
            "evidence_nodes": len(evidence_by_id),
            "claim_nodes": len(claim_nodes),
            "decision_nodes": 1,
            "support_edges": sum(edge["relationship"] == "supports" for edge in edges),
            "all_claims_cited": True,
            "ineligible_evidence_used": False,
        },
        "boundary": "The graph proves declared citation lineage for one synthetic memo; it does not prove source truth or recommendation quality.",
    }


def write_lineage(graph: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = [
        "# Evidence Lineage Report", "", f"- Engagement: `{graph['engagement_id']}`",
        f"- Evidence nodes: {graph['summary']['evidence_nodes']}", f"- Claim nodes: {graph['summary']['claim_nodes']}",
        f"- Support edges: {graph['summary']['support_edges']}", "- Ineligible evidence used: no", "",
        "| From | Relationship | To |", "| --- | --- | --- |",
    ]
    rows.extend(f"| {edge['from']} | {edge['relationship']} | {edge['to']} |" for edge in graph["edges"])
    rows.extend(["", "## Boundary", "", graph["boundary"]])
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
