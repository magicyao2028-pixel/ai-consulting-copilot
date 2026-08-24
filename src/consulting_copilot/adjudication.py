from __future__ import annotations

from datetime import date
from typing import Any


DECISIONS = {"retain_block", "request_recollection", "reconcile"}


def build_adjudication_receipt(
    memo: dict[str, Any],
    *,
    reviewer_alias: str,
    decision: str,
    rationale: str,
    recorded_on: str,
) -> dict[str, Any]:
    """Record a human decision about a conflict without changing the memo."""
    conflicts = memo.get("evidence_conflicts")
    if memo.get("status") != "evidence_conflict" or not isinstance(conflicts, list) or not conflicts:
        raise ValueError("An adjudication receipt requires a blocked evidence-conflict memo")
    if not reviewer_alias.strip() or not rationale.strip():
        raise ValueError("reviewer_alias and rationale must not be blank")
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(sorted(DECISIONS))}")
    try:
        date.fromisoformat(recorded_on)
    except ValueError as exc:
        raise ValueError("recorded_on must use YYYY-MM-DD") from exc
    evidence_ids = sorted({evidence_id for conflict in conflicts for evidence_id in conflict.get("evidence_ids", [])})
    metrics = sorted({str(conflict.get("metric", "")) for conflict in conflicts if str(conflict.get("metric", "")).strip()})
    if not evidence_ids or not metrics:
        raise ValueError("Conflicts must contain evidence IDs and metrics")
    return {
        "schema_version": "1.0",
        "receipt_id": f"ADJ-{memo.get('engagement_id', 'UNKNOWN')}-{recorded_on}",
        "engagement_id": memo.get("engagement_id"),
        "memo_status": memo.get("status"),
        "conflict_metrics": metrics,
        "conflicting_evidence_ids": evidence_ids,
        "reviewer_alias": reviewer_alias.strip(),
        "decision": decision,
        "rationale": rationale.strip(),
        "recorded_on": recorded_on,
        "changes_applied": False,
        "boundary": "This receipt records accountability; it does not promote evidence, rewrite the memo or bypass the conflict block.",
    }


def validate_adjudication_receipt(memo: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "receipt_id", "engagement_id", "memo_status", "conflict_metrics",
        "conflicting_evidence_ids", "reviewer_alias", "decision", "rationale", "recorded_on",
        "changes_applied", "boundary",
    }
    if required.difference(receipt):
        raise ValueError("Adjudication receipt is incomplete")
    if receipt["schema_version"] != "1.0" or receipt["memo_status"] != "evidence_conflict":
        raise ValueError("Adjudication receipt schema or memo status is invalid")
    if receipt["engagement_id"] != memo.get("engagement_id"):
        raise ValueError("Adjudication receipt engagement does not match memo")
    if receipt["decision"] not in DECISIONS:
        raise ValueError("Adjudication decision is unsupported")
    if not isinstance(receipt["changes_applied"], bool) or receipt["changes_applied"]:
        raise ValueError("Adjudication receipt must declare that no changes were applied")
    if not isinstance(receipt["conflict_metrics"], list) or not receipt["conflict_metrics"]:
        raise ValueError("Adjudication receipt must cite conflict metrics")
    if not isinstance(receipt["conflicting_evidence_ids"], list) or not receipt["conflicting_evidence_ids"]:
        raise ValueError("Adjudication receipt must cite conflicting evidence")
    try:
        date.fromisoformat(str(receipt["recorded_on"]))
    except ValueError as exc:
        raise ValueError("Adjudication recorded_on must use YYYY-MM-DD") from exc
    conflict_metrics = {str(item.get("metric")) for item in memo["evidence_conflicts"]}
    conflict_ids = {evidence_id for item in memo["evidence_conflicts"] for evidence_id in item["evidence_ids"]}
    if not set(receipt["conflict_metrics"]).issubset(conflict_metrics) or not set(receipt["conflicting_evidence_ids"]).issubset(conflict_ids):
        raise ValueError("Adjudication receipt cites an unknown conflict")
    return {"receipt_id": receipt["receipt_id"], "decision": receipt["decision"], "passed": True}
