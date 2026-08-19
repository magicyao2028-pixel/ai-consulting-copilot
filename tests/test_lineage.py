import copy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from consulting_copilot import ConsultingCopilot, load_engagement
from consulting_copilot.lineage import build_evidence_lineage, write_lineage


ROOT = Path(__file__).parents[1]


class EvidenceLineageTests(unittest.TestCase):
    def setUp(self):
        self.memo = ConsultingCopilot().analyze(load_engagement(ROOT / "data/sample_engagement.json"))

    def test_builds_complete_lineage_without_ineligible_support(self):
        graph = build_evidence_lineage(self.memo)
        self.assertEqual(graph["summary"]["evidence_nodes"], 6)
        self.assertEqual(graph["summary"]["claim_nodes"], 9)
        self.assertTrue(graph["summary"]["all_claims_cited"])
        self.assertFalse(graph["summary"]["ineligible_evidence_used"])
        self.assertEqual(graph["excluded_evidence_ids"], ["E-05", "E-06"])

    def test_unknown_citation_fails_closed(self):
        memo = copy.deepcopy(self.memo)
        memo["findings"][0]["evidence_ids"] = ["E-UNKNOWN"]
        with self.assertRaisesRegex(ValueError, "Unknown evidence citation"):
            build_evidence_lineage(memo)

    def test_ineligible_evidence_cannot_support_a_claim(self):
        memo = copy.deepcopy(self.memo)
        memo["findings"][0]["evidence_ids"] = ["E-05"]
        with self.assertRaisesRegex(ValueError, "Ineligible evidence"):
            build_evidence_lineage(memo)

    def test_reports_are_reproducible(self):
        graph = build_evidence_lineage(self.memo)
        with TemporaryDirectory() as directory:
            json_path, md_path = Path(directory) / "lineage.json", Path(directory) / "lineage.md"
            write_lineage(graph, json_path, md_path)
            first = (json_path.read_bytes(), md_path.read_bytes())
            write_lineage(graph, json_path, md_path)
            self.assertEqual(first, (json_path.read_bytes(), md_path.read_bytes()))

    def test_non_string_citation_is_rejected(self):
        memo = copy.deepcopy(self.memo)
        memo["findings"][0]["evidence_ids"] = [{"evidence_id": "E-01"}]
        with self.assertRaisesRegex(ValueError, "non-empty evidence ID"):
            build_evidence_lineage(memo)

    def test_malformed_excluded_list_is_rejected(self):
        memo = copy.deepcopy(self.memo)
        memo["stale_evidence"] = None
        with self.assertRaisesRegex(ValueError, "must be lists"):
            build_evidence_lineage(memo)


if __name__ == "__main__":
    unittest.main()
