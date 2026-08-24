import copy
import json
import unittest
from pathlib import Path

from consulting_copilot import ConsultingCopilot, ConsultingEngagement, load_engagement
from consulting_copilot.adjudication import build_adjudication_receipt, validate_adjudication_receipt


ROOT = Path(__file__).parents[1]


class AdjudicationTests(unittest.TestCase):
    def _conflict_memo(self):
        payload = json.loads((ROOT / "data/sample_engagement.json").read_text(encoding="utf-8"))
        payload["evidence"].append({
            "evidence_id": "E-07", "title": "Synthetic conflict extract", "source_type": "internal_record",
            "collected_at": "2026-08-01", "claim": "A second extract reports a five-hour first response.",
            "metric": "first_response_hours", "value": 5, "unit": "hours", "reliability": "verified",
        })
        return ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(payload))

    def test_receipt_records_block_without_mutating_conflict(self):
        memo = self._conflict_memo()
        receipt = build_adjudication_receipt(
            memo,
            reviewer_alias="reviewer-01",
            decision="retain_block",
            rationale="Reconcile current extracts before making a recommendation.",
            recorded_on="2026-08-24",
        )
        self.assertTrue(validate_adjudication_receipt(memo, receipt)["passed"])
        self.assertFalse(receipt["changes_applied"])

    def test_receipt_rejects_non_conflict_memo(self):
        memo = ConsultingCopilot().analyze(load_engagement(ROOT / "data/sample_engagement.json"))
        with self.assertRaisesRegex(ValueError, "blocked evidence-conflict"):
            build_adjudication_receipt(
                memo, reviewer_alias="reviewer-01", decision="retain_block",
                rationale="No conflict.", recorded_on="2026-08-24",
            )

    def test_receipt_rejects_applied_changes(self):
        memo = self._conflict_memo()
        receipt = build_adjudication_receipt(
            memo, reviewer_alias="reviewer-01", decision="retain_block",
            rationale="Keep blocked.", recorded_on="2026-08-24",
        )
        changed = copy.deepcopy(receipt)
        changed["changes_applied"] = True
        with self.assertRaisesRegex(ValueError, "no changes"):
            validate_adjudication_receipt(memo, changed)


if __name__ == "__main__":
    unittest.main()
