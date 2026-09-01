from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any


def summarize_triage_history(outcome_report: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize triage lifecycle records without promoting evidence or executing outreach."""
    if not isinstance(entries, list) or not entries:
        raise ValueError("triage history must be a non-empty list")
    engagement_id = outcome_report.get("engagement_id")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    previous: date | None = None
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("triage history entries must be objects")
        event_id = entry.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip() or event_id in seen:
            raise ValueError("triage history event_id values must be unique and non-blank")
        if entry.get("engagement_id") != engagement_id:
            raise ValueError("triage history engagement_id must match the report")
        status = entry.get("status")
        if status not in {"open", "awaiting_owner_decision", "awaiting_source_reconciliation", "closed"}:
            raise ValueError("triage history status is unsupported")
        try:
            parsed = date.fromisoformat(str(entry.get("recorded_on")))
        except ValueError as exc:
            raise ValueError("triage history recorded_on must be ISO-8601") from exc
        if previous and parsed < previous:
            raise ValueError("triage history must be chronological")
        if entry.get("changes_applied") is not False:
            raise ValueError("triage history changes_applied must remain false")
        seen.add(event_id)
        previous = parsed
        normalized.append({"event_id": event_id, "engagement_id": engagement_id, "status": status, "recorded_on": str(entry["recorded_on"]), "changes_applied": False})
    return {
        "history_version": "0.8",
        "entry_count": len(normalized),
        "status_counts": dict(sorted(Counter(item["status"] for item in normalized).items())),
        "entries": normalized,
        "changes_applied": False,
        "external_actions_executed": 0,
        "evidence_promoted": False,
        "boundary": "History makes triage lifecycle visible only; it does not promote evidence, rewrite the memo or execute outreach.",
    }


__all__ = ["summarize_triage_history"]
