import unittest

from consulting_copilot.feedback_reconciliation import reconcile_feedback_with_triage


class FeedbackReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.history = {
            "evidence_promoted": False, "changes_applied": False,
            "entries": [{"event_id": "E-1", "status": "open"}, {"event_id": "E-2", "status": "awaiting_owner_decision"}],
        }
        self.feedback = [
            {"feedback_id": "F-1", "event_id": "E-1", "recorded_on": "2026-08-20", "status": "accepted", "applied": False},
            {"feedback_id": "F-2", "event_id": "E-2", "recorded_on": "2026-09-01", "status": "pending", "applied": False},
        ]

    def test_reconciles_accepted_and_excludes_pending(self):
        result = reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")
        self.assertEqual((result["reconciled_count"], result["excluded_count"], result["stale_count"]), (1, 1, 1))
        self.assertFalse(result["evidence_promoted"])

    def test_closed_event_is_not_stale(self):
        self.history["entries"][0]["status"] = "closed"
        result = reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")
        self.assertEqual(result["stale_count"], 0)

    def test_rejects_unknown_event(self):
        self.feedback[0]["event_id"] = "E-X"
        with self.assertRaisesRegex(ValueError, "event_id"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")

    def test_rejects_duplicate_feedback(self):
        self.feedback[1]["feedback_id"] = "F-1"
        with self.assertRaisesRegex(ValueError, "unique"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")

    def test_rejects_applied_feedback(self):
        self.feedback[0]["applied"] = True
        with self.assertRaisesRegex(ValueError, "apply changes"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")

    def test_rejects_writing_history(self):
        self.history["evidence_promoted"] = True
        with self.assertRaisesRegex(ValueError, "non-writing"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")

    def test_rejects_invalid_event_status(self):
        self.history["entries"][0]["status"] = "auto_approved"
        with self.assertRaisesRegex(ValueError, "valid"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")

    def test_rejects_invalid_threshold(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08", stale_after_days=0)

    def test_rejects_future_feedback(self):
        self.feedback[0]["recorded_on"] = "2026-09-09"
        with self.assertRaisesRegex(ValueError, "future-dated"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")

    def test_rejects_unknown_feedback_status(self):
        self.feedback[0]["status"] = "auto_approved"
        with self.assertRaisesRegex(ValueError, "feedback status"):
            reconcile_feedback_with_triage(self.feedback, self.history, as_of_date="2026-09-08")


if __name__ == "__main__":
    unittest.main()
