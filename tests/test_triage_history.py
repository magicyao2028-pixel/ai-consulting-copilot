import unittest

from consulting_copilot.triage_history import summarize_triage_history


class TriageHistoryTests(unittest.TestCase):
    def test_history_is_chronological_and_non_executing(self):
        result = summarize_triage_history(
            {"engagement_id": "E-1"},
            [
                {"event_id": "1", "engagement_id": "E-1", "status": "open", "recorded_on": "2026-08-24", "changes_applied": False},
                {"event_id": "2", "engagement_id": "E-1", "status": "closed", "recorded_on": "2026-08-25", "changes_applied": False},
            ],
        )
        self.assertEqual(result["entry_count"], 2)
        self.assertFalse(result["changes_applied"])
        self.assertFalse(result["evidence_promoted"])

    def test_rejects_mismatched_engagement_and_applied_change(self):
        with self.assertRaisesRegex(ValueError, "match"):
            summarize_triage_history({"engagement_id": "E-1"}, [{"event_id": "1", "engagement_id": "E-2", "status": "open", "recorded_on": "2026-08-24", "changes_applied": False}])
        with self.assertRaisesRegex(ValueError, "changes_applied"):
            summarize_triage_history({"engagement_id": "E-1"}, [{"event_id": "1", "engagement_id": "E-1", "status": "open", "recorded_on": "2026-08-24", "changes_applied": True}])


if __name__ == "__main__":
    unittest.main()
