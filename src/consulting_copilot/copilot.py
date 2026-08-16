from __future__ import annotations

from typing import Any

from .models import DEFAULT_THRESHOLDS, ConsultingEngagement, DecisionThresholds, EvidenceItem
from .quality import assess_evidence, select_metrics


REQUIRED_METRICS = {
    "monthly_support_volume",
    "repetitive_contact_share_pct",
    "first_response_hours",
}


class ConsultingCopilot:
    """Builds a deterministic, cited decision memo from structured evidence."""

    def analyze(
        self,
        engagement: ConsultingEngagement,
        thresholds: DecisionThresholds = DEFAULT_THRESHOLDS,
    ) -> dict[str, Any]:
        assessments = assess_evidence(engagement.evidence, engagement.analysis_date)
        eligible = [
            item for item in engagement.evidence
            if assessments[item.evidence_id]["eligible_for_decision"]
        ]
        ignored = [item.evidence_id for item in engagement.evidence if item.reliability == "unverified"]
        stale = [
            item.evidence_id for item in engagement.evidence
            if assessments[item.evidence_id]["freshness_status"] == "stale"
        ]
        future_dated = [
            item.evidence_id for item in engagement.evidence
            if assessments[item.evidence_id]["freshness_status"] == "future_dated"
        ]
        metrics, conflicts = select_metrics(engagement.evidence, assessments)
        if conflicts:
            return self._conflicted(
                engagement, eligible, assessments, ignored, stale, future_dated, conflicts, thresholds
            )
        missing = sorted(REQUIRED_METRICS.difference(metrics))

        if missing:
            return self._insufficient(
                engagement, eligible, assessments, ignored, stale, future_dated, missing, thresholds
            )

        volume = metrics["monthly_support_volume"]
        repetitive = metrics["repetitive_contact_share_pct"]
        response = metrics["first_response_hours"]
        pilot_supported = (
            volume.value >= thresholds.monthly_support_volume
            and repetitive.value >= thresholds.repetitive_contact_share_pct
            and response.value >= thresholds.first_response_hours
        )
        key_ids = [volume.evidence_id, repetitive.evidence_id, response.evidence_id]

        findings = [
            self._claim(
                f"The synthetic support operation handles {volume.value:g} contacts per month.",
                [volume.evidence_id],
            ),
            self._claim(
                (
                    f"Repetitive intents represent {repetitive.value:g}% of contacts, "
                    "creating a bounded assistive use case."
                ),
                [repetitive.evidence_id],
            ),
            self._claim(
                (
                    f"First response currently takes {response.value:g} hours; the active scenario "
                    f"requires at least {thresholds.first_response_hours:g} hours."
                ),
                [response.evidence_id],
            ),
        ]
        risks = self._risks(eligible)
        risk_ids = risks[0]["evidence_ids"] if risks else []
        decision = (
            "Run a 30-day assistive customer-service pilot with human approval gates."
            if pilot_supported
            else "Do not start the pilot yet; the current metrics do not cross the defined thresholds."
        )
        recommendations = [self._claim(decision, key_ids)]
        if risks:
            recommendations.append(self._claim(
                "Keep sensitive-data filtering and human approval as release gates.",
                risk_ids,
            ))

        result = {
            "engagement_id": engagement.engagement_id,
            "analysis_date": engagement.analysis_date,
            "status": "recommendation_ready",
            "decision_question": engagement.decision_question,
            "executive_decision": decision,
            "confidence": "medium",
            "decision_policy": thresholds.as_dict(),
            "pilot_supported": pilot_supported,
            "findings": findings,
            "options": [
                self._claim("Keep the current manual workflow and continue measuring the baseline.", key_ids),
                self._claim("Run a narrow assistive pilot for repetitive intents; recommended.", key_ids),
                self._claim(
                    "Fully automate replies; rejected because current evidence does not support that risk.",
                    key_ids + risk_ids,
                ),
            ],
            "recommendations": recommendations,
            "risks": risks,
            "assumptions": [
                "Synthetic records are directionally representative of the demonstration scenario.",
                "The pilot will not send customer replies without an authorized reviewer.",
            ],
            "pilot_plan": [
                {"days": "1-5", "action": "Confirm baseline definitions, approved intents and privacy gate."},
                {"days": "6-15", "action": "Run shadow-mode suggestions against synthetic or approved test cases."},
                {"days": "16-25", "action": "Review exceptions, false routing and reviewer overrides."},
                {"days": "26-30", "action": "Compare against the baseline and make a human go/no-go decision."},
            ],
            "success_measures": [
                "Median first-response time for the scoped intents",
                "Reviewer acceptance and override rate",
                "Privacy or policy violations (target: zero)",
            ],
            "constraints": list(engagement.constraints),
            "ignored_unverified_evidence": ignored,
            "stale_evidence": stale,
            "future_dated_evidence": future_dated,
            "evidence_conflicts": [],
            "evidence_register": [
                self._evidence_record(item, assessments[item.evidence_id])
                for item in engagement.evidence
            ],
            "governance": {
                "human_approval_required": True,
                "autonomous_customer_action": False,
                "synthetic_public_data": True,
            },
        }
        result["citation_coverage"] = self._citation_coverage(result)
        return result

    def _insufficient(
        self,
        engagement: ConsultingEngagement,
        eligible: list[EvidenceItem],
        assessments: dict[str, dict[str, Any]],
        ignored: list[str],
        stale: list[str],
        future_dated: list[str],
        missing: list[str],
        thresholds: DecisionThresholds,
    ) -> dict[str, Any]:
        result = {
            "engagement_id": engagement.engagement_id,
            "analysis_date": engagement.analysis_date,
            "status": "insufficient_evidence",
            "decision_question": engagement.decision_question,
            "executive_decision": "No recommendation issued.",
            "confidence": "none",
            "decision_policy": thresholds.as_dict(),
            "pilot_supported": None,
            "findings": [self._claim(item.claim, [item.evidence_id]) for item in eligible],
            "options": [],
            "recommendations": [],
            "risks": [],
            "missing_evidence": missing,
            "ignored_unverified_evidence": ignored,
            "stale_evidence": stale,
            "future_dated_evidence": future_dated,
            "evidence_conflicts": [],
            "evidence_register": [
                self._evidence_record(item, assessments[item.evidence_id])
                for item in engagement.evidence
            ],
            "governance": {"human_approval_required": True, "autonomous_customer_action": False},
        }
        result["citation_coverage"] = self._citation_coverage(result)
        return result

    def _conflicted(
        self,
        engagement: ConsultingEngagement,
        eligible: list[EvidenceItem],
        assessments: dict[str, dict[str, Any]],
        ignored: list[str],
        stale: list[str],
        future_dated: list[str],
        conflicts: list[dict[str, Any]],
        thresholds: DecisionThresholds,
    ) -> dict[str, Any]:
        conflict_ids = {evidence_id for item in conflicts for evidence_id in item["evidence_ids"]}
        findings = [
            self._claim(item.claim, [item.evidence_id])
            for item in eligible
            if item.evidence_id in conflict_ids
        ]
        result = {
            "engagement_id": engagement.engagement_id,
            "analysis_date": engagement.analysis_date,
            "status": "evidence_conflict",
            "decision_question": engagement.decision_question,
            "executive_decision": "No recommendation issued until the conflicting evidence is reconciled.",
            "confidence": "none",
            "decision_policy": thresholds.as_dict(),
            "pilot_supported": None,
            "findings": findings,
            "options": [],
            "recommendations": [],
            "risks": [],
            "missing_evidence": [],
            "ignored_unverified_evidence": ignored,
            "stale_evidence": stale,
            "future_dated_evidence": future_dated,
            "evidence_conflicts": conflicts,
            "evidence_register": [
                self._evidence_record(item, assessments[item.evidence_id])
                for item in engagement.evidence
            ],
            "governance": {"human_approval_required": True, "autonomous_customer_action": False},
        }
        result["citation_coverage"] = self._citation_coverage(result)
        return result

    def _risks(self, evidence: list[EvidenceItem]) -> list[dict[str, Any]]:
        privacy = [item for item in evidence if item.metric == "sensitive_data_risk"]
        if not privacy:
            return []
        return [self._claim(
            "Customer messages may contain sensitive data, so raw text must not enter an uncontrolled model path.",
            [item.evidence_id for item in privacy],
        )]

    @staticmethod
    def _claim(text: str, evidence_ids: list[str]) -> dict[str, Any]:
        return {"claim": text, "evidence_ids": evidence_ids}

    @staticmethod
    def _evidence_record(item: EvidenceItem, assessment: dict[str, Any]) -> dict[str, Any]:
        return {
            "evidence_id": item.evidence_id,
            "title": item.title,
            "source_type": item.source_type,
            "collected_at": item.collected_at,
            "claim": item.claim,
            "metric": item.metric,
            "value": item.value,
            "unit": item.unit,
            "reliability": item.reliability,
            "freshness": assessment,
        }

    @staticmethod
    def _citation_coverage(result: dict[str, Any]) -> dict[str, Any]:
        claims = []
        for field in ("findings", "options", "recommendations", "risks"):
            claims.extend(result.get(field, []))
        cited = sum(bool(item.get("evidence_ids")) for item in claims)
        return {
            "cited_claims": cited,
            "total_claims": len(claims),
            "percentage": round(cited / len(claims) * 100, 1) if claims else 100.0,
        }
