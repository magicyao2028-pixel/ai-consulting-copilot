"""Evidence-backed consulting workflow with explicit decision boundaries."""

from .copilot import ConsultingCopilot
from .interviews import normalize_interview_notes, review_candidate_claims
from .models import ConsultingEngagement, EvidenceItem, load_engagement
from .report import render_markdown

__all__ = [
    "ConsultingCopilot", "ConsultingEngagement", "EvidenceItem", "load_engagement",
    "normalize_interview_notes", "review_candidate_claims", "render_markdown",
]
__version__ = "0.3.0"
