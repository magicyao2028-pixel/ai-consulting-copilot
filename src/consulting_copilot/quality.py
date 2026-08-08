from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Iterable

from .models import EvidenceItem


FRESHNESS_LIMIT_DAYS = {
    "internal_record": 60,
    "interview": 90,
    "policy": 365,
    "external_benchmark": 180,
}
RELIABILITY_RANK = {"verified": 2, "indicative": 1, "unverified": 0}
CONFLICT_TOLERANCE = 0.10


def assess_evidence(
    evidence: Iterable[EvidenceItem],
    analysis_date: str,
) -> dict[str, dict[str, Any]]:
    """Describe evidence age and whether it may support a decision."""
    as_of = date.fromisoformat(analysis_date)
    assessments: dict[str, dict[str, Any]] = {}
    for item in evidence:
        collected = date.fromisoformat(item.collected_at)
        age_days = (as_of - collected).days
        max_age_days = FRESHNESS_LIMIT_DAYS[item.source_type]
        reasons: list[str] = []
        if item.reliability == "unverified":
            reasons.append("unverified")
        if age_days < 0:
            freshness_status = "future_dated"
            reasons.append("future_dated")
        elif age_days > max_age_days:
            freshness_status = "stale"
            reasons.append("stale")
        else:
            freshness_status = "current"
        assessments[item.evidence_id] = {
            "age_days": age_days,
            "max_age_days": max_age_days,
            "freshness_status": freshness_status,
            "eligible_for_decision": not reasons,
            "exclusion_reasons": reasons,
        }
    return assessments


def select_metrics(
    evidence: Iterable[EvidenceItem],
    assessments: dict[str, dict[str, Any]],
) -> tuple[dict[str, EvidenceItem], list[dict[str, Any]]]:
    """Select one current item per metric and block material contradictions."""
    grouped: dict[str, list[EvidenceItem]] = defaultdict(list)
    for item in evidence:
        if item.metric and assessments[item.evidence_id]["eligible_for_decision"]:
            grouped[item.metric].append(item)

    selected: dict[str, EvidenceItem] = {}
    conflicts: list[dict[str, Any]] = []
    for metric, items in grouped.items():
        conflict_reason = _conflict_reason(items)
        if conflict_reason:
            conflicts.append({
                "metric": metric,
                "evidence_ids": sorted(item.evidence_id for item in items),
                "values": [
                    {"evidence_id": item.evidence_id, "value": item.value, "unit": item.unit}
                    for item in sorted(items, key=lambda candidate: candidate.evidence_id)
                ],
                "reason": conflict_reason,
            })
            continue
        selected[metric] = sorted(
            items,
            key=lambda item: (-RELIABILITY_RANK[item.reliability], -date.fromisoformat(item.collected_at).toordinal(),
                              item.evidence_id),
        )[0]
    return selected, sorted(conflicts, key=lambda item: item["metric"])


def _conflict_reason(items: list[EvidenceItem]) -> str | None:
    if len(items) < 2:
        return None
    units = {item.unit for item in items}
    if len(units) > 1:
        return "Current evidence uses incompatible units."
    values = [float(item.value) for item in items]
    scale = max(max(abs(value) for value in values), 1.0)
    relative_spread = (max(values) - min(values)) / scale
    if relative_spread > CONFLICT_TOLERANCE:
        return f"Current values differ by {relative_spread:.1%}, above the 10% tolerance."
    return None
