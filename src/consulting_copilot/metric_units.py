"""Declared decision units only; no source audit or automatic conversion."""
from __future__ import annotations

from typing import Any, Iterable


DECISION_METRIC_UNITS = {
    "monthly_support_volume": "contacts/month",
    "repetitive_contact_share_pct": "percent",
    "first_response_hours": "hours",
}


def validate_metric_unit(metric: str | None, unit: Any) -> None:
    if metric in DECISION_METRIC_UNITS:
        expected = DECISION_METRIC_UNITS[metric]
        if not isinstance(unit, str) or unit != expected:
            raise ValueError(f"Decision metric {metric} requires unit '{expected}'; no automatic conversion")


def expected_unit_receipt(evidence: Iterable[Any]) -> dict[str, Any]:
    ids = sorted(item.evidence_id for item in evidence if item.metric in DECISION_METRIC_UNITS)
    return {
        "schema_version": "1.0", "policy_id": "decision-metric-units-v1",
        "required_units": dict(DECISION_METRIC_UNITS),
        "validated_evidence_ids": ids, "validated_metric_count": len(ids),
        "unit_conversion_performed": False, "evidence_mutated": False,
        "human_approval_required": True, "external_actions_executed": 0,
    }


def validate_decision_metric_units(evidence: Iterable[Any]) -> dict[str, Any]:
    from .models import validate_metric_value
    items = tuple(evidence)
    for item in items:
        if item.metric in DECISION_METRIC_UNITS:
            validate_metric_unit(item.metric, item.unit)
            # Public typed-container callers cannot bypass the existing numeric guard.
            validate_metric_value(item.metric, item.value)
    return expected_unit_receipt(items)


def unit_receipt_passed(receipt: dict[str, Any], evidence: Iterable[Any]) -> bool:
    expected = expected_unit_receipt(evidence)
    return (isinstance(receipt, dict) and set(receipt) == set(expected)
            and all(type(receipt[key]) is type(value) and receipt[key] == value for key, value in expected.items()))
