import json
import unittest
from pathlib import Path

from consulting_copilot import (
    ConsultingCopilot,
    ConsultingEngagement,
    DecisionScenario,
    DecisionThresholds,
    compare_scenarios,
    load_engagement,
    load_scenarios,
)


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "data" / "sample_engagement.json"
SCENARIOS = ROOT / "data" / "sample_scenarios.json"


class ScenarioComparisonTests(unittest.TestCase):
    def test_configured_thresholds_change_the_decision(self):
        engagement = load_engagement(SAMPLE)
        strict = DecisionThresholds(5000, 65, 12)
        result = ConsultingCopilot().analyze(engagement, strict)
        self.assertEqual(result["status"], "recommendation_ready")
        self.assertFalse(result["pilot_supported"])
        self.assertEqual(result["decision_policy"]["monthly_support_volume"], 5000)

    def test_sample_comparison_exposes_decision_sensitivity(self):
        result = compare_scenarios(load_engagement(SAMPLE), load_scenarios(SCENARIOS))
        self.assertEqual(result["status"], "comparison_ready")
        self.assertEqual(result["scenario_count"], 3)
        self.assertTrue(result["decision_changes_across_scenarios"])
        self.assertEqual([item["pilot_supported"] for item in result["scenarios"]], [True, True, False])

    def test_scenarios_reuse_governed_evidence_and_exclude_vendor_claim(self):
        result = compare_scenarios(load_engagement(SAMPLE), load_scenarios(SCENARIOS))
        self.assertTrue(result["governance"]["same_evidence_register_used"])
        self.assertTrue(result["governance"]["candidate_claims_are_not_evidence"])
        self.assertTrue(all("E-05" not in item["evidence_ids_used"] for item in result["scenarios"]))

    def test_evidence_conflict_blocks_every_scenario(self):
        payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        payload["evidence"].append({
            "evidence_id": "E-07",
            "title": "Synthetic conflicting extract",
            "source_type": "internal_record",
            "collected_at": "2026-08-01",
            "claim": "A current extract reports a five-hour first response.",
            "metric": "first_response_hours",
            "value": 5,
            "unit": "hours",
            "reliability": "verified",
        })
        result = compare_scenarios(ConsultingEngagement.from_mapping(payload), load_scenarios(SCENARIOS))
        self.assertEqual(result["status"], "comparison_blocked")
        self.assertEqual(result["blocked_statuses"], ["evidence_conflict"])
        self.assertTrue(all(item["pilot_supported"] is None for item in result["scenarios"]))

    def test_threshold_validation_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            DecisionThresholds.from_mapping({
                "monthly_support_volume": 1000,
                "repetitive_contact_share_pct": 101,
                "first_response_hours": 8,
            })

    def test_threshold_validation_rejects_nan_and_infinity(self):
        for invalid in ("NaN", "Infinity"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "finite"):
                    DecisionThresholds.from_mapping({
                        "monthly_support_volume": invalid,
                        "repetitive_contact_share_pct": 40,
                        "first_response_hours": 8,
                    })

    def test_comparison_requires_two_scenarios(self):
        one = DecisionScenario("only", "Only scenario", DecisionThresholds(1000, 40, 8))
        with self.assertRaisesRegex(ValueError, "At least two"):
            compare_scenarios(load_engagement(SAMPLE), [one])


if __name__ == "__main__":
    unittest.main()
