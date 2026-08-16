from __future__ import annotations

from typing import Any, Iterable

from .copilot import ConsultingCopilot
from .models import ConsultingEngagement, DecisionScenario


def compare_scenarios(
    engagement: ConsultingEngagement,
    scenarios: Iterable[DecisionScenario],
) -> dict[str, Any]:
    """Run one governed evidence set against declared policy scenarios."""
    scenario_list = tuple(scenarios)
    if len(scenario_list) < 2:
        raise ValueError("At least two scenarios are required for comparison")

    results = []
    for scenario in scenario_list:
        memo = ConsultingCopilot().analyze(engagement, scenario.thresholds)
        results.append({
            "scenario_id": scenario.scenario_id,
            "label": scenario.label,
            "status": memo["status"],
            "pilot_supported": memo["pilot_supported"],
            "executive_decision": memo["executive_decision"],
            "thresholds": memo["decision_policy"],
            "evidence_ids_used": _used_evidence_ids(memo),
            "blocking_conflicts": memo.get("evidence_conflicts", []),
            "missing_evidence": memo.get("missing_evidence", []),
        })

    blocked_statuses = sorted({item["status"] for item in results if item["status"] != "recommendation_ready"})
    decisions = {item["pilot_supported"] for item in results if item["pilot_supported"] is not None}
    return {
        "engagement_id": engagement.engagement_id,
        "analysis_date": engagement.analysis_date,
        "status": "comparison_blocked" if blocked_statuses else "comparison_ready",
        "scenario_count": len(results),
        "decision_changes_across_scenarios": len(decisions) > 1,
        "blocked_statuses": blocked_statuses,
        "scenarios": results,
        "governance": {
            "same_evidence_register_used": True,
            "thresholds_change_policy_not_evidence": True,
            "candidate_claims_are_not_evidence": True,
            "human_approval_required": True,
        },
    }


def _used_evidence_ids(memo: dict[str, Any]) -> list[str]:
    used = {
        evidence_id
        for field in ("findings", "options", "recommendations", "risks")
        for claim in memo.get(field, [])
        for evidence_id in claim.get("evidence_ids", [])
    }
    return sorted(used)
