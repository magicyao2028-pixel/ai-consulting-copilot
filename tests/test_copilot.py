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
        self.assertIn("Stale evidence: E-06", markdown)

    def test_sample_contains_only_declared_evidence_ids(self):
        result = ConsultingCopilot().analyze(load_engagement(SAMPLE))
        declared = {item["evidence_id"] for item in result["evidence_register"]}
        for field in ("findings", "options", "recommendations", "risks"):
            for claim in result[field]:
                self.assertTrue(set(claim["evidence_ids"]).issubset(declared))

    def test_flags_stale_evidence_without_using_it(self):
        result = ConsultingCopilot().analyze(load_engagement(SAMPLE))
        self.assertEqual(result["stale_evidence"], ["E-06"])
        record = next(item for item in result["evidence_register"] if item["evidence_id"] == "E-06")
        self.assertEqual(record["freshness"]["freshness_status"], "stale")
        self.assertFalse(record["freshness"]["eligible_for_decision"])

    def test_stale_required_metric_causes_abstention(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        response = next(
            item for item in payload["evidence"] if item.get("metric") == "first_response_hours"
        )
        response["collected_at"] = "2025-01-01"
        result = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(payload))
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertIn("first_response_hours", result["missing_evidence"])
        self.assertIn("E-03", result["stale_evidence"])

    def test_blocks_materially_conflicting_current_metrics(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["evidence"].append({
            "evidence_id": "E-07",
            "title": "Synthetic second response-time extract",
            "source_type": "internal_record",
            "collected_at": "2026-08-01",
            "claim": "A second current extract reports a five-hour first response.",
            "metric": "first_response_hours",
            "value": 5,
            "unit": "hours",
            "reliability": "verified",
        })
        result = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(payload))
        self.assertEqual(result["status"], "evidence_conflict")
        self.assertEqual(result["executive_decision"],
                         "No recommendation issued until the conflicting evidence is reconciled.")
        self.assertEqual(result["evidence_conflicts"][0]["metric"], "first_response_hours")
        self.assertEqual(result["recommendations"], [])

    def test_accepts_current_duplicate_metrics_within_tolerance(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["evidence"].append({
            "evidence_id": "E-07",
            "title": "Synthetic cross-check",
            "source_type": "internal_record",
            "collected_at": "2026-08-01",
            "claim": "A cross-check reports an 11.5-hour first response.",
            "metric": "first_response_hours",
            "value": 11.5,
            "unit": "hours",
            "reliability": "verified",
        })
        result = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(payload))
        self.assertEqual(result["status"], "recommendation_ready")
        self.assertEqual(result["evidence_conflicts"], [])

    def test_future_dated_required_metric_is_not_eligible(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        response = next(
            item for item in payload["evidence"] if item.get("metric") == "first_response_hours"
        )
        response["collected_at"] = "2026-08-09"
        result = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(payload))
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertIn("E-03", result["future_dated_evidence"])

    def test_rejects_invalid_analysis_date(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["context"]["analysis_date"] = "08/08/2026"
        with self.assertRaisesRegex(ValueError, "analysis_date"):
            ConsultingEngagement.from_mapping(payload)


if __name__ == "__main__":
    unittest.main()
