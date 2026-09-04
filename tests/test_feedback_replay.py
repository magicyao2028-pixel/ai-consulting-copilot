import unittest

from consulting_copilot.feedback_replay import replay_reviewer_feedback


HISTORY = {"entries": [{"event_id": "E-1"}, {"event_id": "E-2"}]}


def record(**overrides):
    value = {"feedback_id": "FB-1", "event_id": "E-1", "recorded_on": "2026-08-26", "classification": "usability", "status": "accepted", "summary": "clearer queue", "applied": False}
    value.update(overrides)
    return value


class FeedbackReplayTests(unittest.TestCase):
    def test_accepted_replayed_pending_excluded(self):
        result = replay_reviewer_feedback([record(), record(feedback_id="FB-2", event_id="E-2", status="pending")], HISTORY)
        self.assertEqual(result["replayed_count"], 1)
        self.assertEqual(result["excluded_count"], 1)
        self.assertFalse(result["changes_applied"])
        self.assertFalse(result["evidence_promoted"])

    def test_rejected_excluded(self):
        result = replay_reviewer_feedback([record(status="rejected")], HISTORY)
        self.assertEqual(result["replayed_count"], 0)
        self.assertEqual(result["excluded_count"], 1)

    def test_unknown_event_blocked(self):
        with self.assertRaisesRegex(ValueError, "event_id"):
            replay_reviewer_feedback([record(event_id="UNKNOWN")], HISTORY)

    def test_duplicate_id_blocked(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            replay_reviewer_feedback([record(), record(event_id="E-2")], HISTORY)

    def test_non_chronological_dates_blocked(self):
        with self.assertRaisesRegex(ValueError, "chronological"):
            replay_reviewer_feedback([record(recorded_on="2026-08-27"), record(feedback_id="FB-2", event_id="E-2", recorded_on="2026-08-26")], HISTORY)

    def test_applied_feedback_blocked(self):
        with self.assertRaisesRegex(ValueError, "apply"):
            replay_reviewer_feedback([record(applied=True)], HISTORY)

    def test_invalid_classification_blocked(self):
        with self.assertRaisesRegex(ValueError, "classification"):
            replay_reviewer_feedback([record(classification="unknown")], HISTORY)

    def test_empty_batch_blocked(self):
        with self.assertRaisesRegex(ValueError, "non-empty"):
            replay_reviewer_feedback([], HISTORY)


if __name__ == "__main__":
    unittest.main()
