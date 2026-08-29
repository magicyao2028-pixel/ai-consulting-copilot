from __future__ import annotations

from typing import Any


_OUTCOMES = {
    "keep_release_block_and_request_owner_decision": (
        "awaiting_owner_decision",
        "An accountable owner confirms whether the evidence block remains in force.",
    ),
    "collect_targeted_recollection_for_conflicting_metrics": (
        "awaiting_targeted_recollection",
        "A reviewed source resolves the conflicting metric before recommendation.",
    ),
    "compare_conflicting_sources_before_recommendation": (
        "awaiting_source_reconciliation",
        "An accountable reviewer documents the source comparison and its effect on the conflict.",
    ),
}


def build_triage_outcome_report(triage: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    """Expose a bounded triage lifecycle without executing the recommended action."""
    if triage.get("status") != "blocked_pending_human_decision" or triage.get("changes_applied") is not False:
        raise ValueError("Triage must remain blocked and unapplied")
    if triage.get("external_actions_executed") != 0 or not triage.get("human_approval_required"):
        raise ValueError("Triage must remain non-executing and human-gated")
    action = triage.get("recommended_next_action")
    outcome = _OUTCOMES.get(action)
    if outcome is None:
        raise ValueError("Triage action is unsupported")
    if receipt.get("decision") != triage.get("adjudication_decision"):
        raise ValueError("Triage receipt decision does not match")
    owner_action_status, completion_criteria = outcome
    return {
        "schema_version": "1.0",
        "report_version": "0.7",
        "engagement_id": triage.get("engagement_id"),
        "status": "open",
        "severity": triage.get("severity"),
        "conflict_count": triage.get("conflict_count"),
        "conflict_metrics": list(triage.get("conflict_metrics", [])),
        "conflicting_evidence_ids": list(triage.get("conflicting_evidence_ids", [])),
        "adjudication_receipt_id": receipt.get("receipt_id"),
        "adjudication_decision": triage.get("adjudication_decision"),
        "recommended_next_action": action,
        "owner_action_status": owner_action_status,
        "completion_criteria": completion_criteria,
        "changes_applied": False,
        "external_actions_executed": 0,
        "human_approval_required": True,
        "boundary": "This report makes triage status visible for review; it does not promote evidence, rewrite a memo or execute outreach.",
    }
