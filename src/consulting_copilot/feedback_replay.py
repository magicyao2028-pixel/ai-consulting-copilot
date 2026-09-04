from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any


_STATUSES = {"accepted", "pending", "rejected"}
_CLASSIFICATIONS = {"defect", "requirement", "usability", "performance", "safety", "documentation"}


def replay_reviewer_feedback(feedback_batch: list[dict[str, Any]], current_history: dict[str, Any]) -> dict[str, Any]:
    """Replay accepted synthetic feedback as advisory regression metadata only."""
    if not isinstance(feedback_batch, list) or not feedback_batch:
        raise ValueError("feedback batch must be a non-empty list")
    event_ids = {str(item.get("event_id")) for item in current_history.get("entries", [])}
    if not event_ids:
        raise ValueError("current triage history must contain entries")
    seen: set[str] = set()
    dates: list[date] = []
    statuses: Counter[str] = Counter()
    replayed: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for record in feedback_batch:
        if not isinstance(record, dict):
            raise ValueError("each feedback record must be an object")
        required = {"feedback_id", "event_id", "recorded_on", "classification", "status", "summary", "applied"}
        if required.difference(record):
            raise ValueError("feedback record is incomplete")
        feedback_id = str(record["feedback_id"]).strip()
        if not feedback_id or feedback_id in seen:
            raise ValueError("feedback IDs must be unique")
        seen.add(feedback_id)
        event_id = str(record["event_id"]).strip()
        if event_id not in event_ids:
            raise ValueError("feedback event_id must reference current triage history")
        try:
            recorded_on = date.fromisoformat(str(record["recorded_on"]))
        except ValueError as exc:
            raise ValueError("feedback recorded_on must be ISO format") from exc
        if dates and recorded_on < dates[-1]:
            raise ValueError("feedback dates must be chronological")
        dates.append(recorded_on)
        status = str(record["status"]).strip()
        classification = str(record["classification"]).strip()
        if status not in _STATUSES or classification not in _CLASSIFICATIONS or not str(record["summary"]).strip():
            raise ValueError("feedback status, classification or summary is invalid")
        if record["applied"] is not False:
            raise ValueError("feedback replay cannot apply changes")
        item = {"feedback_id": feedback_id, "event_id": event_id, "status": status, "passed": True}
        statuses[status] += 1
        (replayed if status == "accepted" else excluded).append(item)
    return {
        "schema_version": "1.0",
        "record_count": len(feedback_batch),
        "status_counts": dict(sorted(statuses.items())),
        "replayed_count": len(replayed),
        "excluded_count": len(excluded),
        "replayed": replayed,
        "excluded": excluded,
        "changes_applied": False,
        "evidence_promoted": False,
        "memo_rewritten": False,
        "external_actions_executed": 0,
        "boundary": "Only accepted synthetic feedback is replayed as advisory regression metadata; no evidence is promoted, memo is rewritten or outreach is executed.",
    }


__all__ = ["replay_reviewer_feedback"]
