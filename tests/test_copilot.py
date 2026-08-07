import json
import unittest
from pathlib import Path

from consulting_copilot import ConsultingCopilot, ConsultingEngagement, load_engagement, render_markdown


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "data" / "sample_engagement.json"


class ConsultingCopilotTests(unittest.TestCase):
    def test_builds_recommendation_with_complete_claim_citations(self):
        result = ConsultingCopilot().analyze(load_engagement(SAMPLE))
        self.assertEqual(result["status"], "recommendation_ready")
        self.assertIn("30-day", result["executive_decision"])
        self.assertEqual(result["citation_coverage"]["percentage"], 100.0)

    def test_ignores_unverified_vendor_claim(self):
        result = ConsultingCopilot().analyze(load_engagement(SAMPLE))
        self.assertEqual(result["ignored_unverified_evidence"], ["E-05"])
        used_ids = {
            evidence_id
            for field in ("findings", "options", "recommendations", "risks")
            for claim in result[field]
            for evidence_id in claim["evidence_ids"]
        }
        self.assertNotIn("E-05", used_ids)

    def test_abstains_when_required_metric_is_missing(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["evidence"] = [
            item for item in payload["evidence"] if item.get("metric") != "first_response_hours"
        ]
        result = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(payload))
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["executive_decision"], "No recommendation issued.")
        self.assertIn("first_response_hours", result["missing_evidence"])

    def test_rejects_duplicate_evidence_ids(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["evidence"][1]["evidence_id"] = payload["evidence"][0]["evidence_id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            ConsultingEngagement.from_mapping(payload)

    def test_privacy_risk_creates_release_gate(self):
        result = ConsultingCopilot().analyze(load_engagement(SAMPLE))
        self.assertTrue(result["risks"])
        self.assertIn("E-04", result["risks"][0]["evidence_ids"])
        self.assertTrue(result["governance"]["human_approval_required"])
        self.assertFalse(result["governance"]["autonomous_customer_action"])

    def test_markdown_contains_citations_and_evidence_register(self):
        markdown = render_markdown(ConsultingCopilot().analyze(load_engagement(SAMPLE)))
        self.assertIn("[E-01]", markdown)
        self.assertIn("## Evidence register", markdown)
        self.assertIn("Ignored unverified evidence: E-05", markdown)

    def test_sample_contains_only_declared_evidence_ids(self):
        result = ConsultingCopilot().analyze(load_engagement(SAMPLE))
        declared = {item["evidence_id"] for item in result["evidence_register"]}
        for field in ("findings", "options", "recommendations", "risks"):
            for claim in result[field]:
                self.assertTrue(set(claim["evidence_ids"]).issubset(declared))


if __name__ == "__main__":
    unittest.main()
