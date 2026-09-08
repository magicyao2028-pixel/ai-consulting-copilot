from __future__ import annotations

from datetime import date, timedelta
from typing import Any


_EVENT_STATUSES = {"open", "awaiting_owner_decision", "awaiting_source_reconciliation", "closed"}
_FEEDBACK_STATUSES = {"accepted", "pending", "rejected"}


def reconcile_feedback_with_triage(
    feedback_batch: list[dict[str, Any]], history: dict[str, Any], *, as_of_date: str, stale_after_days: int = 7
) -> dict[str, Any]:
    """Reconcile feedback with current triage state without promoting evidence or outreach."""
    if stale_after_days < 1:
        raise ValueError("stale_after_days must be at least 1")
    try:
        as_of = date.fromisoformat(as_of_date)
    except ValueError as exc:
        raise ValueError("as_of_date must be ISO format") from exc
    if not isinstance(history, dict) or history.get("evidence_promoted") is not False or history.get("changes_applied") is not False:
        raise ValueError("triage history must remain non-writing")
    entries = history.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("triage history must contain entries")
    event_status: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("triage history entries must be objects")
        event_id = str(entry.get("event_id", "")).strip()
        status = str(entry.get("status", "")).strip()
        if not event_id or event_id in event_status or status not in _EVENT_STATUSES:
            raise ValueError("triage history events must be unique and valid")
        event_status[event_id] = status
    if not isinstance(feedback_batch, list) or not feedback_batch:
        raise ValueError("feedback batch must be a non-empty list")

    cutoff = as_of - timedelta(days=stale_after_days)
    seen: set[str] = set()
    reconciled: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for record in feedback_batch:
        if not isinstance(record, dict):
            raise ValueError("feedback records must be objects")
        feedback_id = str(record.get("feedback_id", "")).strip()
        event_id = str(record.get("event_id", "")).strip()
        if not feedback_id or feedback_id in seen:
            raise ValueError("feedback IDs must be unique")
        seen.add(feedback_id)
        if event_id not in event_status:
            raise ValueError("feedback event_id must reference current triage history")
        try:
            recorded_on = date.fromisoformat(str(record.get("recorded_on", "")))
        except ValueError as exc:
            raise ValueError("feedback recorded_on must be ISO format") from exc
        if recorded_on > as_of:
            raise ValueError("feedback cannot be future-dated")
        if record.get("applied") is not False:
            raise ValueError("feedback reconciliation cannot apply changes")
        status = str(record.get("status", "")).strip()
        if status not in _FEEDBACK_STATUSES:
            raise ValueError("feedback status must be accepted, pending or rejected")
        item = {"feedback_id": feedback_id, "event_id": event_id, "feedback_status": status, "triage_status": event_status[event_id]}
        if status != "accepted":
            excluded.append(item)
            continue
        item["stale"] = recorded_on <= cutoff and event_status[event_id] != "closed"
        reconciled.append(item)
    return {
        "schema_version": "1.0",
        "as_of_date": as_of.isoformat(),
        "cutoff_date": cutoff.isoformat(),
        "reconciled_count": len(reconciled),
        "excluded_count": len(excluded),
        "stale_count": sum(bool(item["stale"]) for item in reconciled),
        "reconciled": reconciled,
        "excluded": excluded,
        "changes_applied": False,
        "evidence_promoted": False,
        "memo_rewritten": False,
        "external_actions_executed": 0,
        "boundary": "Reconciliation exposes accepted feedback still attached to open triage events; it does not promote evidence, rewrite the memo or execute outreach.",
    }


__all__ = ["reconcile_feedback_with_triage"]
