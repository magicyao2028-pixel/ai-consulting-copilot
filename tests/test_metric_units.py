import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from consulting_copilot import ConsultingCopilot, ConsultingEngagement, load_engagement
from consulting_copilot.models import DEFAULT_THRESHOLDS, load_scenarios
from consulting_copilot.scenarios import compare_scenarios
from consulting_copilot.trial import run_trial

ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "data/sample_engagement.json"


class DecisionMetricUnitTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(SAMPLE.read_text())
        self.engagement = load_engagement(SAMPLE)

    def test_known_metrics_reject_wrong_missing_and_coerced_units(self):
        for index, wrong in ((0, "contacts/day"), (1, "ratio"), (2, "minutes")):
            for unit in (wrong, None, "", " ", 1, False, [], {}, " hours "):
                bad = copy.deepcopy(self.payload)
                bad["evidence"][index]["unit"] = unit
                before = copy.deepcopy(bad)
                with self.assertRaisesRegex(ValueError, "requires unit"):
                    ConsultingEngagement.from_mapping(bad)
                self.assertEqual(bad, before)
            bad = copy.deepcopy(self.payload)
            bad["evidence"][index].pop("unit")
            with self.assertRaisesRegex(ValueError, "requires unit"):
                ConsultingEngagement.from_mapping(bad)

    def test_direct_typed_container_cannot_bypass_units_before_claim_generation(self):
        bad = replace(self.engagement, evidence=tuple(
            replace(item, unit="minutes", value=24) if item.metric == "first_response_hours" else item
            for item in self.engagement.evidence))
        before = copy.deepcopy(bad)
        with patch("consulting_copilot.copilot.assess_evidence") as assessment:
            with self.assertRaisesRegex(ValueError, "requires unit"):
                ConsultingCopilot().analyze(bad)
            assessment.assert_not_called()
        self.assertEqual(bad, before)

    def test_existing_finite_numeric_guard_is_preserved_for_typed_decision_metrics(self):
        for value in (float("nan"), float("inf"), True, -1):
            bad = replace(self.engagement, evidence=tuple(
                replace(item, value=value) if item.metric == "first_response_hours" else item
                for item in self.engagement.evidence))
            with self.assertRaises(ValueError):
                ConsultingCopilot().analyze(bad)

    def test_permissive_scenarios_do_not_convert_or_bypass_units(self):
        scenarios = load_scenarios(ROOT / "data/sample_scenarios.json")
        bad = replace(self.engagement, evidence=tuple(
            replace(item, unit="minutes") if item.metric == "first_response_hours" else item
            for item in self.engagement.evidence))
        with self.assertRaisesRegex(ValueError, "requires unit"):
            compare_scenarios(bad, scenarios)

    def test_valid_ready_memo_exposes_exact_receipt_and_preserves_evidence(self):
        before = copy.deepcopy(self.engagement)
        memo = ConsultingCopilot().analyze(self.engagement)
        self.assertEqual(memo["decision_metric_unit_receipt"], {
            "schema_version": "1.0", "policy_id": "decision-metric-units-v1",
            "required_units": {"monthly_support_volume": "contacts/month", "repetitive_contact_share_pct": "percent", "first_response_hours": "hours"},
            "validated_evidence_ids": ["E-01", "E-02", "E-03"], "validated_metric_count": 3,
            "unit_conversion_performed": False, "evidence_mutated": False,
            "human_approval_required": True, "external_actions_executed": 0,
        })
        self.assertEqual(self.engagement, before)
        self.assertIs(memo["pilot_supported"], True)

    def test_insufficient_and_conflict_memos_also_bind_unit_receipts(self):
        missing = replace(self.engagement, evidence=tuple(item for item in self.engagement.evidence if item.metric != "first_response_hours"))
        memo = ConsultingCopilot().analyze(missing)
        self.assertEqual(memo["status"], "insufficient_evidence")
        self.assertEqual(memo["decision_metric_unit_receipt"]["validated_metric_count"], 2)
        conflicting = replace(self.engagement, evidence=self.engagement.evidence + (replace(self.engagement.evidence[2], evidence_id="E-07", value=5),))
        memo = ConsultingCopilot().analyze(conflicting)
        self.assertEqual(memo["status"], "evidence_conflict")
        self.assertEqual(memo["decision_metric_unit_receipt"]["validated_evidence_ids"], ["E-01", "E-02", "E-03", "E-07"])
        self.assertIs(memo["decision_metric_unit_receipt"]["evidence_mutated"], False)

    def test_non_decision_metrics_keep_their_declared_units(self):
        self.payload["evidence"][5]["unit"] = "custom_domain_hours"
        memo = ConsultingCopilot().analyze(ConsultingEngagement.from_mapping(self.payload))
        self.assertEqual(memo["evidence_register"][5]["unit"], "custom_domain_hours")
        self.assertNotIn("E-06", memo["decision_metric_unit_receipt"]["validated_evidence_ids"])

    def test_five_negative_trial_probes_reject_without_mutating_evidence(self):
        report = run_trial(ROOT)
        self.assertIs(report["decision_metric_units"]["passed"], True)
        self.assertEqual(len(report["decision_metric_units"]["negative_probes"]), 5)
        self.assertTrue(all(item["rejected"] and item["evidence_mutated"] is False for item in report["decision_metric_units"]["negative_probes"]))
        self.assertEqual(len(report["evidence_index"]), 14)

    def test_every_actual_receipt_field_is_required_by_trial_pass(self):
        original = ConsultingCopilot.analyze
        receipt = original(ConsultingCopilot(), self.engagement)["decision_metric_unit_receipt"]
        for key, value in receipt.items():
            def altered_analyze(agent, engagement, thresholds=DEFAULT_THRESHOLDS):
                memo = original(agent, engagement, thresholds)
                memo["decision_metric_unit_receipt"][key] = not value if type(value) is bool else "tampered"
                return memo
            with patch.object(ConsultingCopilot, "analyze", altered_analyze):
                report = run_trial(ROOT)
            self.assertFalse(report["overall_passed"], key)
            self.assertEqual(report["decision_metric_units"]["receipt"][key], not value if type(value) is bool else "tampered")
        for key in ("unit_conversion_performed", "evidence_mutated", "human_approval_required", "external_actions_executed"):
            def altered_type(agent, engagement, thresholds=DEFAULT_THRESHOLDS):
                memo = original(agent, engagement, thresholds)
                memo["decision_metric_unit_receipt"][key] = int(receipt[key]) if type(receipt[key]) is bool else False
                return memo
            with patch.object(ConsultingCopilot, "analyze", altered_type):
                self.assertFalse(run_trial(ROOT)["overall_passed"], key)

    def test_returned_triage_history_replay_reconciliation_governance_is_required(self):
        report = run_trial(ROOT)
        targets = [
            ("build_conflict_triage", "conflict_triage", ("changes_applied",), ("human_approval_required",)),
            ("build_triage_outcome_report", "triage_outcome_report", ("changes_applied",), ("human_approval_required",)),
            ("summarize_triage_history", "triage_history", ("changes_applied", "evidence_promoted"), ()),
            ("replay_reviewer_feedback", "feedback_replay", ("changes_applied", "evidence_promoted", "memo_rewritten"), ()),
            ("reconcile_feedback_with_triage", "feedback_reconciliation", ("changes_applied", "evidence_promoted", "memo_rewritten"), ()),
        ]
        for function, key, false_fields, true_fields in targets:
            for field in false_fields + true_fields + ("external_actions_executed",):
                bad = copy.deepcopy(report[key])
                bad[field] = False if field in true_fields else True if field in false_fields else 1
                with patch("consulting_copilot.trial." + function, return_value=bad):
                    try:
                        altered = run_trial(ROOT)
                    except ValueError:
                        continue  # A downstream fail-closed gate also denies Trial PASS.
                self.assertFalse(altered["overall_passed"], (key, field))

    def test_invalid_unit_cli_creates_no_memo_output(self):
        from consulting_copilot.cli import main
        self.payload["evidence"][2]["unit"] = "minutes"
        with TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "memo.json"
            input_path.write_text(json.dumps(self.payload))
            with patch("sys.argv", ["consulting-copilot", str(input_path), "--json-output", str(output_path)]):
                with self.assertRaisesRegex(ValueError, "requires unit"):
                    main()
            self.assertFalse(output_path.exists())

    def test_actual_memo_governance_is_typed_and_required_by_trial(self):
        original = ConsultingCopilot.analyze
        for field, replacement in (("human_approval_required", False), ("autonomous_customer_action", True), ("synthetic_public_data", False)):
            def altered_analyze(agent, engagement, thresholds=DEFAULT_THRESHOLDS):
                memo = original(agent, engagement, thresholds)
                if field in memo["governance"]:
                    memo["governance"][field] = replacement
                return memo
            with patch.object(ConsultingCopilot, "analyze", altered_analyze):
                report = run_trial(ROOT)
            self.assertFalse(report["overall_passed"], field)
            self.assertEqual(report["memo_governance"][field], replacement)
