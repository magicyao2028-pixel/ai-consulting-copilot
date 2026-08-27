from __future__ import annotations

from typing import Any


def build_conflict_triage(memo: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    """Turn a validated adjudication receipt into a non-executing work item."""
    conflicts = memo.get("evidence_conflicts")
    if memo.get("status") != "evidence_conflict" or not isinstance(conflicts, list) or not conflicts:
        raise ValueError("Conflict triage requires a blocked evidence-conflict memo")
    if receipt.get("memo_status") != "evidence_conflict" or receipt.get("engagement_id") != memo.get("engagement_id"):
        raise ValueError("Conflict triage receipt does not match memo")
    decision = receipt.get("decision")
    actions = {
        "retain_block": "keep_release_block_and_request_owner_decision",
        "request_recollection": "collect_targeted_recollection_for_conflicting_metrics",
        "reconcile": "compare_conflicting_sources_before_recommendation",
    }
    if decision not in actions:
        raise ValueError("Conflict triage decision is unsupported")
    metrics = sorted({str(item.get("metric", "")) for item in conflicts if str(item.get("metric", "")).strip()})
    evidence_ids = sorted({evidence_id for item in conflicts for evidence_id in item.get("evidence_ids", [])})
    return {
        "schema_version": "1.0",
        "triage_type": "evidence-conflict work item",
        "engagement_id": memo.get("engagement_id"),
        "status": "blocked_pending_human_decision",
        "severity": "high" if len(conflicts) >= 2 else "medium",
        "conflict_count": len(conflicts),
        "conflict_metrics": metrics,
        "conflicting_evidence_ids": evidence_ids,
        "adjudication_decision": decision,
        "recommended_next_action": actions[decision],
        "changes_applied": False,
        "external_actions_executed": 0,
        "human_approval_required": True,
        "boundary": "This triage item organizes follow-up only; it does not promote evidence, rewrite the memo or execute outreach.",
    }
