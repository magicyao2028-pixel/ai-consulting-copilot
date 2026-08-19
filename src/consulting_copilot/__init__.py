"""Evidence-backed consulting workflow with explicit decision boundaries."""

from .copilot import ConsultingCopilot
from .interviews import normalize_interview_notes, review_candidate_claims
from .models import (
    DEFAULT_THRESHOLDS,
    ConsultingEngagement,
    DecisionScenario,
    DecisionThresholds,
    EvidenceItem,
    load_engagement,
    load_scenarios,
)
from .report import render_markdown
from .scenarios import compare_scenarios
from .lineage import build_evidence_lineage, write_lineage

__all__ = [
    "DEFAULT_THRESHOLDS", "ConsultingCopilot", "ConsultingEngagement", "DecisionScenario",
    "DecisionThresholds", "EvidenceItem", "compare_scenarios", "load_engagement", "load_scenarios",
    "normalize_interview_notes", "review_candidate_claims", "render_markdown",
    "build_evidence_lineage", "write_lineage",
]
__version__ = "0.5.0"
