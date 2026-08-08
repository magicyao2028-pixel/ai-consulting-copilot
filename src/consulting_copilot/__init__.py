"""Evidence-backed consulting workflow with explicit decision boundaries."""

from .copilot import ConsultingCopilot
from .models import ConsultingEngagement, EvidenceItem, load_engagement
from .report import render_markdown

__all__ = ["ConsultingCopilot", "ConsultingEngagement", "EvidenceItem", "load_engagement", "render_markdown"]
__version__ = "0.2.0"
