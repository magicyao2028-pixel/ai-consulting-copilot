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
from .adjudication import build_adjudication_receipt, validate_adjudication_receipt

__all__ = [
    "DEFAULT_THRESHOLDS", "ConsultingCopilot", "ConsultingEngagement", "DecisionScenario",
    "DecisionThresholds", "EvidenceItem", "compare_scenarios", "load_engagement", "load_scenarios",
    "normalize_interview_notes", "review_candidate_claims", "render_markdown",
    "build_evidence_lineage", "write_lineage", "build_adjudication_receipt", "validate_adjudication_receipt",
]
__version__ = "0.6.0"
