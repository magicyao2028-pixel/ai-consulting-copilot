from __future__ import annotations

import copy
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .copilot import ConsultingCopilot
from .adjudication import validate_adjudication_receipt
from .lineage import build_evidence_lineage
from .models import ConsultingEngagement, load_engagement


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


def run_trial(root: Path) -> dict[str, Any]:
    root = root.resolve()
    engagement_path = root / "data/sample_engagement.json"
    memo = ConsultingCopilot().analyze(load_engagement(engagement_path))
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
    adjudication = validate_adjudication_receipt(conflict_memo, load_json_object(root / "evidence/adjudication_receipt.json"))
    evidence = validate_evidence_index(root, load_json_object(root / "evidence/evidence_index.json"))
    external = validate_external_intake(load_json_object(root / "evidence/external_intake.json"))
    feedback = validate_feedback(root, load_json_object(root / "evidence/feedback_case.json"))
    core_passed = memo["status"] == "recommendation_ready" and graph["summary"]["claim_nodes"] == 9 and graph["summary"]["all_claims_cited"] and not graph["summary"]["ineligible_evidence_used"] and failure_closed and conflict_memo["status"] == "evidence_conflict" and adjudication["passed"]
    return {
        "schema_version": "1.0", "trial_id": "TRIAL-CONSULTING-001", "source_data": "synthetic",
        "overall_passed": core_passed and feedback["passed"] and all(item["passed"] for item in evidence + external),
        "core_flow": {"passed": core_passed, "memo_status": memo["status"], "evidence_nodes": graph["summary"]["evidence_nodes"], "claim_nodes": graph["summary"]["claim_nodes"], "unknown_citation_blocked": failure_closed, "external_actions_executed": 0},
        "feedback_regression": feedback, "external_intake": external, "adjudication": adjudication, "evidence_index": evidence,
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
        f"- Cited claim nodes: {report['core_flow']['claim_nodes']}", f"- Unknown citation blocked: {'yes' if report['core_flow']['unknown_citation_blocked'] else 'no'}", f"- Conflict adjudication receipt: {'pass' if report['adjudication']['passed'] else 'fail'}", "",
        "## Pilot boundary", "", *[f"- {item}" for item in report["boundaries"]], "",
    ]), encoding="utf-8")
    return report
