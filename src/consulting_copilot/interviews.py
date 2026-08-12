from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


CLAIM_KINDS = {"observation", "opinion", "request"}
REVIEW_DECISIONS = {"approve", "reject", "needs_clarification"}


@dataclass(frozen=True)
class InterviewStatement:
    statement_id: str
    text: str
    claim_kind: str
    topic: str
    metric: str | None
    value: float | None
    unit: str | None

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "InterviewStatement":
        kind = str(value.get("claim_kind", "")).strip()
        if kind not in CLAIM_KINDS:
            raise ValueError(f"claim_kind must be one of: {', '.join(sorted(CLAIM_KINDS))}")
        metric = str(value.get("metric", "")).strip() or None
        raw_value = value.get("value")
        numeric_value = float(raw_value) if raw_value is not None else None
        item = cls(
            statement_id=str(value.get("statement_id", "")).strip(),
            text=" ".join(str(value.get("text", "")).split()),
            claim_kind=kind,
            topic=str(value.get("topic", "")).strip(),
            metric=metric,
            value=numeric_value,
            unit=str(value.get("unit", "")).strip() or None,
        )
        if not all((item.statement_id, item.text, item.topic)):
            raise ValueError("statement_id, text and topic must not be blank")
        if (item.metric is None) != (item.value is None):
            raise ValueError("metric and value must be supplied together")
        if item.metric is not None and item.unit is None:
            raise ValueError("unit is required for a metric statement")
        return item


@dataclass(frozen=True)
class InterviewNote:
    note_id: str
    conducted_at: str
    participant_role: str
    synthetic: bool
    consent_for_analysis: bool
    statements: tuple[InterviewStatement, ...]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "InterviewNote":
        raw_statements = value.get("statements")
        if not isinstance(raw_statements, list) or not raw_statements:
            raise ValueError("statements must be a non-empty list")
        statements = tuple(InterviewStatement.from_mapping(item) for item in raw_statements)
        statement_ids = [item.statement_id for item in statements]
        if len(statement_ids) != len(set(statement_ids)):
            raise ValueError("statement_id values must be unique within a note")
        note = cls(
            note_id=str(value.get("note_id", "")).strip(),
            conducted_at=str(value.get("conducted_at", "")).strip(),
            participant_role=str(value.get("participant_role", "")).strip(),
            synthetic=value.get("synthetic") is True,
            consent_for_analysis=value.get("consent_for_analysis") is True,
            statements=statements,
        )
        if not all((note.note_id, note.conducted_at, note.participant_role)):
            raise ValueError("note_id, conducted_at and participant_role must not be blank")
        try:
            date.fromisoformat(note.conducted_at)
        except ValueError as exc:
            raise ValueError("conducted_at must use YYYY-MM-DD") from exc
        if not note.synthetic:
            raise ValueError("public interview fixtures must be explicitly synthetic")
        if not note.consent_for_analysis:
            raise ValueError("consent_for_analysis must be true before normalization")
        return note


def normalize_interview_notes(payload: dict[str, Any]) -> dict[str, Any]:
    engagement_id = str(payload.get("engagement_id", "")).strip()
    raw_notes = payload.get("notes")
    if not engagement_id:
        raise ValueError("engagement_id must not be blank")
    if not isinstance(raw_notes, list) or not raw_notes:
        raise ValueError("notes must be a non-empty list")
    notes = tuple(InterviewNote.from_mapping(item) for item in raw_notes)
    note_ids = [item.note_id for item in notes]
    if len(note_ids) != len(set(note_ids)):
        raise ValueError("note_id values must be unique")

    candidates: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    for note in notes:
        for statement in note.statements:
            safe_note = re.sub(r"[^A-Za-z0-9]+", "-", note.note_id).strip("-").upper()
            safe_statement = re.sub(r"[^A-Za-z0-9]+", "-", statement.statement_id).strip("-").upper()
            claim_id = f"CLM-{safe_note}-{safe_statement}"
            if claim_id in claim_ids:
                raise ValueError("normalized claim_id values must be unique")
            claim_ids.add(claim_id)
            candidates.append({
                "claim_id": claim_id,
                "candidate_claim": statement.text,
                "claim_kind": statement.claim_kind,
                "topic": statement.topic,
                "metric": statement.metric,
                "value": statement.value,
                "unit": statement.unit,
                "source_note_id": note.note_id,
                "source_statement_id": statement.statement_id,
                "source_role": note.participant_role,
                "collected_at": note.conducted_at,
                "approval_status": "pending_human_approval",
                "eligible_for_evidence_register": False,
            })
    return {
        "engagement_id": engagement_id,
        "status": "awaiting_human_review",
        "candidate_claims": candidates,
        "evidence_register": [],
        "summary": {
            "notes_normalized": len(notes),
            "candidate_claims": len(candidates),
            "approved_evidence_items": 0,
        },
        "governance": {
            "human_approval_required": True,
            "automatic_evidence_promotion": False,
            "synthetic_public_data": True,
        },
    }


def review_candidate_claims(normalization: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    reviewer_id = str(review.get("reviewer_id", "")).strip()
    reviewed_at = str(review.get("reviewed_at", "")).strip()
    if not reviewer_id or not reviewed_at:
        raise ValueError("reviewer_id and reviewed_at must not be blank")
    try:
        date.fromisoformat(reviewed_at)
    except ValueError as exc:
        raise ValueError("reviewed_at must use YYYY-MM-DD") from exc
    raw_decisions = review.get("decisions")
    if not isinstance(raw_decisions, list) or not raw_decisions:
        raise ValueError("decisions must be a non-empty list")
    candidates = normalization.get("candidate_claims")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("normalization must contain candidate_claims")
    candidate_by_id = {str(item.get("claim_id")): item for item in candidates}
    if len(candidate_by_id) != len(candidates):
        raise ValueError("candidate claim IDs must be unique")

    decision_by_id: dict[str, dict[str, str]] = {}
    for item in raw_decisions:
        claim_id = str(item.get("claim_id", "")).strip()
        decision = str(item.get("decision", "")).strip()
        rationale = str(item.get("rationale", "")).strip()
        if claim_id not in candidate_by_id:
            raise ValueError(f"unknown claim_id in review: {claim_id}")
        if claim_id in decision_by_id:
            raise ValueError("each claim_id may be reviewed only once")
        if decision not in REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of: {', '.join(sorted(REVIEW_DECISIONS))}")
        if not rationale:
            raise ValueError("every review decision requires a rationale")
        decision_by_id[claim_id] = {"decision": decision, "rationale": rationale}

    reviewed_claims: list[dict[str, Any]] = []
    evidence_register: list[dict[str, Any]] = []
    for candidate in candidates:
        decision = decision_by_id.get(candidate["claim_id"])
        rendered = dict(candidate)
        if decision is None:
            rendered["review"] = None
            reviewed_claims.append(rendered)
            continue
        approved = decision["decision"] == "approve" and candidate["claim_kind"] == "observation"
        effective_decision = decision["decision"] if candidate["claim_kind"] == "observation" else (
            "rejected_by_claim_kind_control" if decision["decision"] == "approve" else decision["decision"]
        )
        rendered.update({
            "approval_status": effective_decision,
            "eligible_for_evidence_register": approved,
            "review": {"reviewer_id": reviewer_id, "reviewed_at": reviewed_at, **decision},
        })
        reviewed_claims.append(rendered)
        if approved:
            evidence_register.append({
                "evidence_id": f"INT-{candidate['claim_id']}",
                "title": f"Approved synthetic interview observation: {candidate['topic']}",
                "source_type": "interview",
                "collected_at": candidate["collected_at"],
                "claim": candidate["candidate_claim"],
                "metric": candidate["metric"],
                "value": candidate["value"],
                "unit": candidate["unit"],
                "reliability": "indicative",
                "provenance": {
                    "claim_id": candidate["claim_id"],
                    "source_note_id": candidate["source_note_id"],
                    "source_statement_id": candidate["source_statement_id"],
                    "reviewer_id": reviewer_id,
                    "reviewed_at": reviewed_at,
                },
            })
    return {
        "engagement_id": normalization.get("engagement_id"),
        "status": "human_review_recorded",
        "reviewed_claims": reviewed_claims,
        "evidence_register": evidence_register,
        "summary": {
            "candidate_claims": len(candidates),
            "reviewed_claims": len(decision_by_id),
            "approved_evidence_items": len(evidence_register),
            "pending_claims": len(candidates) - len(decision_by_id),
        },
        "governance": {
            "human_approval_required": True,
            "automatic_evidence_promotion": False,
            "approved_observations_only": True,
            "synthetic_public_data": True,
        },
    }


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("input file must contain a JSON object")
    return payload
