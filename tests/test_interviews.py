import json
import unittest
from pathlib import Path

from consulting_copilot import ConsultingCopilot, ConsultingEngagement
from consulting_copilot.interviews import normalize_interview_notes, review_candidate_claims


ROOT = Path(__file__).parents[1]
NOTES = ROOT / "data" / "sample_interview_notes.json"
REVIEW = ROOT / "data" / "sample_claim_review.json"
ENGAGEMENT = ROOT / "data" / "sample_engagement.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class InterviewGovernanceTests(unittest.TestCase):
    def test_normalization_never_promotes_evidence(self):
        result = normalize_interview_notes(load(NOTES))
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertEqual(result["summary"]["candidate_claims"], 5)
        self.assertEqual(result["evidence_register"], [])
        self.assertTrue(all(not item["eligible_for_evidence_register"] for item in result["candidate_claims"]))

    def test_human_review_promotes_only_approved_observations(self):
        normalized = normalize_interview_notes(load(NOTES))
        result = review_candidate_claims(normalized, load(REVIEW))
        self.assertEqual(result["summary"]["approved_evidence_items"], 3)
        self.assertTrue(all(item["reliability"] == "indicative" for item in result["evidence_register"]))
        self.assertTrue(all(item["provenance"]["reviewer_id"] for item in result["evidence_register"]))

    def test_approved_opinion_is_blocked_by_claim_kind_control(self):
        normalized = normalize_interview_notes(load(NOTES))
        review = {"reviewer_id": "TEST-REVIEWER", "reviewed_at": "2026-08-12", "decisions": [{
            "claim_id": "CLM-INT-OPS-001-S-03", "decision": "approve", "rationale": "Boundary test."
        }]}
        result = review_candidate_claims(normalized, review)
        claim = next(item for item in result["reviewed_claims"] if item["claim_id"].endswith("S-03"))
        self.assertEqual(claim["approval_status"], "rejected_by_claim_kind_control")
        self.assertEqual(result["evidence_register"], [])

    def test_requires_explicit_consent(self):
        payload = load(NOTES)
        payload["notes"][0]["consent_for_analysis"] = False
        with self.assertRaisesRegex(ValueError, "consent"):
            normalize_interview_notes(payload)

    def test_rejects_duplicate_note_ids(self):
        payload = load(NOTES)
        payload["notes"][1]["note_id"] = payload["notes"][0]["note_id"]
        with self.assertRaisesRegex(ValueError, "note_id"):
            normalize_interview_notes(payload)

    def test_rejects_unknown_claim_review(self):
        review = load(REVIEW)
        review["decisions"][0]["claim_id"] = "CLM-UNKNOWN"
        with self.assertRaisesRegex(ValueError, "unknown claim_id"):
            review_candidate_claims(normalize_interview_notes(load(NOTES)), review)

    def test_rejects_duplicate_review_decisions(self):
        review = load(REVIEW)
        review["decisions"].append(dict(review["decisions"][0]))
        with self.assertRaisesRegex(ValueError, "only once"):
            review_candidate_claims(normalize_interview_notes(load(NOTES)), review)

    def test_approved_metric_still_passes_existing_conflict_gate(self):
        notes = load(NOTES)
        notes["notes"][0]["statements"][1].update({"metric": "first_response_hours", "value": 20, "unit": "hours"})
        normalized = normalize_interview_notes(notes)
        review = {"reviewer_id": "TEST-REVIEWER", "reviewed_at": "2026-08-12", "decisions": [{
            "claim_id": "CLM-INT-OPS-001-S-02", "decision": "approve", "rationale": "Integration test."
        }]}
        approved = review_candidate_claims(normalized, review)["evidence_register"]
        engagement = load(ENGAGEMENT)
        engagement["context"]["analysis_date"] = "2026-08-12"
        engagement["evidence"].extend(approved)
        result = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(engagement))
        self.assertEqual(result["status"], "evidence_conflict")


if __name__ == "__main__":
    unittest.main()
