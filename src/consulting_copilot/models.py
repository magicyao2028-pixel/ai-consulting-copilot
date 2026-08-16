from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


RELIABILITY_LEVELS = {"verified", "indicative", "unverified"}
SOURCE_TYPES = {"internal_record", "interview", "policy", "external_benchmark"}


@dataclass(frozen=True)
class DecisionThresholds:
    monthly_support_volume: float
    repetitive_contact_share_pct: float
    first_response_hours: float

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "DecisionThresholds":
        required = {
            "monthly_support_volume",
            "repetitive_contact_share_pct",
            "first_response_hours",
        }
        missing = sorted(required.difference(value))
        if missing:
            raise ValueError(f"Missing threshold fields: {', '.join(missing)}")
        thresholds = cls(**{field: float(value[field]) for field in required})
        if not all(math.isfinite(item) for item in thresholds.as_dict().values()):
            raise ValueError("Decision thresholds must be finite numbers")
        if thresholds.monthly_support_volume < 0 or thresholds.first_response_hours < 0:
            raise ValueError("Volume and response-hour thresholds must not be negative")
        if not 0 <= thresholds.repetitive_contact_share_pct <= 100:
            raise ValueError("Repetitive-contact threshold must be between 0 and 100")
        return thresholds

    def as_dict(self) -> dict[str, float]:
        return {
            "monthly_support_volume": self.monthly_support_volume,
            "repetitive_contact_share_pct": self.repetitive_contact_share_pct,
            "first_response_hours": self.first_response_hours,
        }


DEFAULT_THRESHOLDS = DecisionThresholds(
    monthly_support_volume=1000,
    repetitive_contact_share_pct=40,
    first_response_hours=8,
)


@dataclass(frozen=True)
class DecisionScenario:
    scenario_id: str
    label: str
    thresholds: DecisionThresholds

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "DecisionScenario":
        thresholds = value.get("thresholds")
        if not isinstance(thresholds, dict):
            raise ValueError("scenario thresholds must be an object")
        scenario = cls(
            scenario_id=str(value.get("scenario_id", "")).strip(),
            label=str(value.get("label", "")).strip(),
            thresholds=DecisionThresholds.from_mapping(thresholds),
        )
        if not scenario.scenario_id or not scenario.label:
            raise ValueError("scenario_id and label must not be blank")
        return scenario


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    title: str
    source_type: str
    collected_at: str
    claim: str
    metric: str | None
    value: float | None
    unit: str | None
    reliability: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "EvidenceItem":
        required = {"evidence_id", "title", "source_type", "collected_at", "claim", "reliability"}
        missing = sorted(required.difference(value))
        if missing:
            raise ValueError(f"Missing evidence fields: {', '.join(missing)}")
        source_type = str(value["source_type"]).strip()
        reliability = str(value["reliability"]).strip()
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"source_type must be one of: {', '.join(sorted(SOURCE_TYPES))}")
        if reliability not in RELIABILITY_LEVELS:
            raise ValueError(f"reliability must be one of: {', '.join(sorted(RELIABILITY_LEVELS))}")
        metric = str(value.get("metric", "")).strip() or None
        raw_value = value.get("value")
        numeric_value = float(raw_value) if raw_value is not None else None
        item = cls(
            evidence_id=str(value["evidence_id"]).strip(),
            title=str(value["title"]).strip(),
            source_type=source_type,
            collected_at=str(value["collected_at"]).strip(),
            claim=str(value["claim"]).strip(),
            metric=metric,
            value=numeric_value,
            unit=str(value.get("unit", "")).strip() or None,
            reliability=reliability,
        )
        if not all((item.evidence_id, item.title, item.collected_at, item.claim)):
            raise ValueError("Evidence text fields must not be blank")
        try:
            date.fromisoformat(item.collected_at)
        except ValueError as exc:
            raise ValueError("collected_at must use YYYY-MM-DD") from exc
        if (item.metric is None) != (item.value is None):
            raise ValueError("metric and value must be supplied together")
        return item


@dataclass(frozen=True)
class ConsultingEngagement:
    engagement_id: str
    decision_question: str
    company_profile: str
    decision_owner: str
    analysis_date: str
    horizon_days: int
    constraints: tuple[str, ...]
    evidence: tuple[EvidenceItem, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ConsultingEngagement":
        context = value.get("context")
        if not isinstance(context, dict):
            raise ValueError("context must be an object")
        evidence_payload = value.get("evidence")
        if not isinstance(evidence_payload, list) or not evidence_payload:
            raise ValueError("evidence must be a non-empty list")
        constraints = value.get("constraints", [])
        if not isinstance(constraints, list) or not all(isinstance(item, str) for item in constraints):
            raise ValueError("constraints must be a list of strings")
        evidence = tuple(EvidenceItem.from_mapping(item) for item in evidence_payload)
        ids = [item.evidence_id for item in evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence_id values must be unique")
        engagement = cls(
            engagement_id=str(value.get("engagement_id", "")).strip(),
            decision_question=str(value.get("decision_question", "")).strip(),
            company_profile=str(context.get("company_profile", "")).strip(),
            decision_owner=str(context.get("decision_owner", "")).strip(),
            analysis_date=str(context.get("analysis_date", "")).strip(),
            horizon_days=int(context.get("horizon_days", 0)),
            constraints=tuple(item.strip() for item in constraints if item.strip()),
            evidence=evidence,
        )
        if not all((engagement.engagement_id, engagement.decision_question, engagement.company_profile,
                    engagement.decision_owner, engagement.analysis_date)):
            raise ValueError("Engagement identity, question and context fields must not be blank")
        try:
            date.fromisoformat(engagement.analysis_date)
        except ValueError as exc:
            raise ValueError("analysis_date must use YYYY-MM-DD") from exc
        if engagement.horizon_days < 1:
            raise ValueError("horizon_days must be at least 1")
        return engagement


def load_engagement(path: Path) -> ConsultingEngagement:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid engagement JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Engagement file must contain a JSON object")
    return ConsultingEngagement.from_mapping(payload)


def load_scenarios(path: Path) -> tuple[DecisionScenario, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid scenario JSON: {exc.msg}") from exc
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Scenario file must contain at least two scenarios")
    scenarios = tuple(DecisionScenario.from_mapping(item) for item in payload)
    ids = [item.scenario_id for item in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("scenario_id values must be unique")
    return scenarios
