from __future__ import annotations

import copy
import json
import re
from datetime import date
from dataclasses import replace
from pathlib import Path
from typing import Any

from .copilot import ConsultingCopilot
from .adjudication import validate_adjudication_receipt
from .conflict_triage import build_conflict_triage
from .triage_report import build_triage_outcome_report
from .triage_history import summarize_triage_history
from .feedback_replay import replay_reviewer_feedback
from .feedback_reconciliation import reconcile_feedback_with_triage
from .lineage import build_evidence_lineage
from .models import ConsultingEngagement, load_engagement
from .metric_units import unit_receipt_passed


COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def validate_evidence_index(root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Evidence index must contain claims")
    root = root.resolve()
    seen: set[str] = set()
    checks = []
    for claim in claims:
        claim_id = str(claim.get("claim_id", "")).strip() if isinstance(claim, dict) else ""
        artifacts = claim.get("artifacts") if isinstance(claim, dict) else None
        if not claim_id or claim_id in seen or not str(claim.get("statement", "")).strip() or not isinstance(artifacts, list) or not artifacts:
            raise ValueError("Evidence claims must be unique and complete")
        seen.add(claim_id)
        paths = []
        for artifact in artifacts:
            relative = str(artifact.get("path", "")) if isinstance(artifact, dict) else ""
            target = (root / relative).resolve()
            if not isinstance(artifact, dict) or not str(artifact.get("kind", "")).strip() or not relative or not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Missing, unsafe or untyped evidence path: {relative}")
            paths.append(relative)
        checks.append({"claim_id": claim_id, "artifact_paths": paths, "passed": True})
    return checks


def validate_external_intake(payload: dict[str, Any]) -> list[dict[str, Any]]:
    date.fromisoformat(str(payload.get("reviewed_on", "")))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("External intake must contain candidates")
    checks = []
    for item in candidates:
        required = {"repository", "version", "commit", "license", "decision", "code_adopted", "reason"}
        if not isinstance(item, dict) or required.difference(item):
            raise ValueError("External candidate metadata is incomplete")
        if not str(item["repository"]).startswith("https://github.com/") or not COMMIT_PATTERN.fullmatch(str(item["commit"])):
            raise ValueError("External repository or full commit SHA is invalid")
        if item["decision"] not in {"adopted", "rejected"} or not isinstance(item["code_adopted"], bool) or (item["decision"] == "adopted") != item["code_adopted"]:
            raise ValueError("External decision is invalid or inconsistent")
        checks.append({"repository": item["repository"], "decision": item["decision"], "passed": True})
    return checks


def validate_feedback(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    required = {"feedback_id", "source_type", "recorded_on", "classification", "decision", "summary", "acceptance_test", "implementation", "release_result"}
    if required.difference(payload) or any(not str(payload[key]).strip() for key in required):
        raise ValueError("Feedback record is incomplete")
    date.fromisoformat(str(payload["recorded_on"]))
    if payload["source_type"] not in {"real", "synthetic"} or payload["classification"] not in {"defect", "requirement", "usability", "performance", "safety", "documentation"}:
        raise ValueError("Feedback source_type or classification is unsupported")
    if payload["decision"] != "accepted":
        raise ValueError("Trial feedback case must be accepted")
    for key in ("acceptance_test", "implementation"):
        target = (root.resolve() / str(payload[key])).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"Feedback {key} path is missing or unsafe")
    return {"feedback_id": payload["feedback_id"], "source_type": payload["source_type"], "passed": True}


METRIC_UNIT_PROBES = (
    ("hours_as_minutes", "first_response_hours", "minutes"),
    ("volume_per_day", "monthly_support_volume", "contacts/day"),
    ("share_as_ratio", "repetitive_contact_share_pct", "ratio"),
    ("missing_hours_unit", "first_response_hours", None),
)


def metric_unit_trial_passed(report: Any, engagement: ConsultingEngagement) -> bool:
    """Bind the final returned receipt and every exact typed negative outcome."""
    if not isinstance(report, dict) or set(report) != {"passed", "receipt", "negative_probes"}:
        return False
    if report["passed"] is not True or not unit_receipt_passed(report["receipt"], engagement.evidence):
        return False
    expected = [(name, metric, "mapping") for name, metric, _ in METRIC_UNIT_PROBES]
    expected.append(("typed_hours_as_minutes", "first_response_hours", "typed_container"))
    probes = report["negative_probes"]
    return (type(probes) is list and len(probes) == len(expected)
            and all(isinstance(probe, dict)
                    and set(probe) == {"probe_id", "metric", "input_route", "rejected", "evidence_mutated"}
                    and type(probe["probe_id"]) is str and probe["probe_id"] == name
                    and type(probe["metric"]) is str and probe["metric"] == metric
                    and type(probe["input_route"]) is str and probe["input_route"] == route
                    and probe["rejected"] is True and probe["evidence_mutated"] is False
                    for probe, (name, metric, route) in zip(probes, expected)))


def run_metric_unit_trial(payload: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    engagement = ConsultingEngagement.from_mapping(payload)
    probes = []
    for name, metric, unit in METRIC_UNIT_PROBES:
        bad = copy.deepcopy(payload)
        next(item for item in bad["evidence"] if item.get("metric") == metric)["unit"] = unit
        before = copy.deepcopy(bad)
        rejected = False
        try:
            ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(bad))
        except ValueError as exc:
            rejected = "requires unit" in str(exc)
        probes.append({"probe_id": name, "metric": metric, "input_route": "mapping", "rejected": rejected,
                       "evidence_mutated": before != bad})
    bad_engagement = replace(engagement, evidence=tuple(
        replace(item, unit="minutes") if item.metric == "first_response_hours" else item
        for item in engagement.evidence))
    before = copy.deepcopy(bad_engagement)
    rejected = False
    try:
        ConsultingCopilot().analyze(bad_engagement)
    except ValueError as exc:
        rejected = "requires unit" in str(exc)
    probes.append({"probe_id": "typed_hours_as_minutes", "metric": "first_response_hours", "input_route": "typed_container", "rejected": rejected,
                   "evidence_mutated": before != bad_engagement})
    return {"passed": unit_receipt_passed(receipt, engagement.evidence)
                      and all(item["rejected"] and not item["evidence_mutated"] for item in probes),
            "receipt": receipt, "negative_probes": probes}


def run_trial(root: Path) -> dict[str, Any]:
    root = root.resolve()
    engagement_path = root / "data/sample_engagement.json"
    engagement = load_engagement(engagement_path)
    memo = ConsultingCopilot().analyze(engagement)
    metric_units = run_metric_unit_trial(load_json_object(engagement_path), memo["decision_metric_unit_receipt"])
    graph = build_evidence_lineage(memo)
    bad_memo = copy.deepcopy(memo)
    bad_memo["findings"][0]["evidence_ids"] = ["E-UNKNOWN"]
    failure_closed = False
    try:
        build_evidence_lineage(bad_memo)
    except ValueError as exc:
        failure_closed = "Unknown evidence citation" in str(exc)
    conflict_payload = json.loads(engagement_path.read_text(encoding="utf-8"))
    conflict_payload["evidence"].append({
        "evidence_id": "E-07", "title": "Synthetic conflict extract", "source_type": "internal_record",
        "collected_at": "2026-08-01", "claim": "A second extract reports a five-hour first response.",
        "metric": "first_response_hours", "value": 5, "unit": "hours", "reliability": "verified",
    })
    conflict_memo = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(conflict_payload))
    receipt_payload = load_json_object(root / "evidence/adjudication_receipt.json")
    adjudication = validate_adjudication_receipt(conflict_memo, receipt_payload)
    triage = build_conflict_triage(conflict_memo, receipt_payload)
    triage_report = build_triage_outcome_report(triage, receipt_payload)
    triage_history = summarize_triage_history(
        triage_report,
        json.loads((root / "data/triage_history.json").read_text(encoding="utf-8")),
    )
    feedback_replay = replay_reviewer_feedback(
        json.loads((root / "data/reviewer_feedback.json").read_text(encoding="utf-8")),
        triage_history,
    )
    feedback_reconciliation = reconcile_feedback_with_triage(
        json.loads((root / "data/reviewer_feedback.json").read_text(encoding="utf-8")),
        triage_history,
        as_of_date="2026-09-08",
    )
    evidence = validate_evidence_index(root, load_json_object(root / "evidence/evidence_index.json"))
    external = validate_external_intake(load_json_object(root / "evidence/external_intake.json"))
    feedback = validate_feedback(root, load_json_object(root / "evidence/feedback_case.json"))
    governance_passed = (
        memo["governance"]["human_approval_required"] is True
        and memo["governance"]["autonomous_customer_action"] is False
        and memo["governance"]["synthetic_public_data"] is True
        and conflict_memo["governance"]["human_approval_required"] is True
        and conflict_memo["governance"]["autonomous_customer_action"] is False
        and unit_receipt_passed(conflict_memo["decision_metric_unit_receipt"], ConsultingEngagement.from_mapping(conflict_payload).evidence)
        and triage["human_approval_required"] is True
        and triage_report["human_approval_required"] is True
        and all(item["changes_applied"] is False for item in triage_history["entries"])
        and triage_history["changes_applied"] is False
        and feedback_replay["evidence_promoted"] is False and feedback_replay["memo_rewritten"] is False
        and feedback_reconciliation["changes_applied"] is False and feedback_reconciliation["memo_rewritten"] is False
        and all(type(item["external_actions_executed"]) is int and item["external_actions_executed"] == 0
                for item in (triage, triage_report, triage_history, feedback_replay, feedback_reconciliation))
    )
    returned_receipt = metric_units.get("receipt") if isinstance(metric_units, dict) else None
    returned_action_count = returned_receipt.get("external_actions_executed") if isinstance(returned_receipt, dict) else None
    action_counts = [item["external_actions_executed"] for item in (triage, triage_report, triage_history, feedback_replay, feedback_reconciliation)] + [returned_action_count]
    actual_action_count = sum(action_counts) if all(type(value) is int for value in action_counts) else None
    core_passed = metric_unit_trial_passed(metric_units, engagement) and governance_passed and memo["status"] == "recommendation_ready" and graph["summary"]["claim_nodes"] == 9 and graph["summary"]["all_claims_cited"] and not graph["summary"]["ineligible_evidence_used"] and failure_closed and conflict_memo["status"] == "evidence_conflict" and adjudication["passed"] is True and triage["status"] == "blocked_pending_human_decision" and triage["changes_applied"] is False and triage_report["status"] == "open" and triage_report["changes_applied"] is False and triage_report["external_actions_executed"] == 0 and triage_history["entry_count"] == 2 and triage_history["evidence_promoted"] is False and feedback_replay["replayed_count"] == 1 and feedback_replay["excluded_count"] == 1 and feedback_replay["changes_applied"] is False and feedback_reconciliation["reconciled_count"] == 1 and feedback_reconciliation["excluded_count"] == 1 and feedback_reconciliation["stale_count"] == 1 and feedback_reconciliation["evidence_promoted"] is False
    return {
        "schema_version": "1.0", "trial_id": "TRIAL-CONSULTING-001", "source_data": "synthetic",
        "decision_metric_units": metric_units,
        "overall_passed": core_passed and feedback["passed"] and all(item["passed"] for item in evidence + external),
        "core_flow": {"passed": core_passed, "memo_status": memo["status"], "evidence_nodes": graph["summary"]["evidence_nodes"], "claim_nodes": graph["summary"]["claim_nodes"], "unknown_citation_blocked": failure_closed, "external_actions_executed": actual_action_count},
        "memo_governance": memo["governance"], "conflict_memo_governance": conflict_memo["governance"],
        "feedback_regression": feedback, "feedback_replay": feedback_replay, "feedback_reconciliation": feedback_reconciliation, "external_intake": external, "adjudication": adjudication, "conflict_triage": triage, "triage_outcome_report": triage_report, "triage_history": triage_history, "evidence_index": evidence,
        "boundaries": load_json_object(root / "evidence/evidence_index.json")["boundaries"],
    }


def write_trial_report(root: Path, json_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = run_trial(root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text("\n".join([
        "# Consulting Copilot Trial Readiness", "", "> Synthetic offline verification; no model call, research claim or business action is executed.", "",
        f"- Overall: **{'PASS' if report['overall_passed'] else 'FAIL'}**", f"- Memo status: `{report['core_flow']['memo_status']}`",
        f"- Decision metric unit contract: {'PASS' if report['decision_metric_units']['passed'] else 'FAIL'}; {len(report['decision_metric_units']['negative_probes'])} negative probes",
        f"- Cited claim nodes: {report['core_flow']['claim_nodes']}", f"- Unknown citation blocked: {'yes' if report['core_flow']['unknown_citation_blocked'] else 'no'}", f"- Conflict adjudication receipt: {'pass' if report['adjudication']['passed'] else 'fail'}", f"- Conflict triage: `{report['conflict_triage']['recommended_next_action']}`", f"- Triage outcome status: `{report['triage_outcome_report']['owner_action_status']}`", f"- Reviewer feedback replay: {report['feedback_replay']['replayed_count']} accepted, {report['feedback_replay']['excluded_count']} excluded", f"- Feedback reconciliation: {report['feedback_reconciliation']['reconciled_count']} reconciled, {report['feedback_reconciliation']['stale_count']} stale", "",
        "## Pilot boundary", "", *[f"- {item}" for item in report["boundaries"]], "",
    ]), encoding="utf-8")
    return report
