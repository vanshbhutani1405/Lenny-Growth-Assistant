import logging
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)


class WorkflowIntent(StrEnum):
    GROUNDED_QA = "grounded_qa"
    RESEARCH_SYNTHESIS = "research_synthesis"
    SHIP30 = "ship30"


@dataclass(frozen=True, slots=True)
class WorkflowPlan:
    intent: WorkflowIntent
    instruction: str
    requires_ship30_validation: bool = False

    def prompt(self, query: str, top_k: int | None = None) -> str:
        top_k_instruction = f" Use at most {top_k} retrieval results." if top_k else ""
        return f"{self.instruction}\n\nUser request: {query}{top_k_instruction}"


class WorkflowRouter:
    """Deterministic intent router shared by Claude and Ollama workflows."""

    _ship30_terms = ("ship 30", "ship30", "essay", "newsletter", "write a post", "blog post")
    _research_terms = (
        "research", "synthesize", "synthesis", "compare", "contrast", "patterns",
        "themes", "across episodes", "what do multiple", "summarize the advice",
    )

    def route(self, query: str) -> WorkflowPlan:
        normalized = " ".join(query.lower().split())
        if any(term in normalized for term in self._ship30_terms):
            plan = WorkflowPlan(
                WorkflowIntent.SHIP30,
                """Use search_transcripts before drafting. Transform grounded transcript evidence into a Ship 30 for 30-style essay of approximately 1,250 words. Include a strong hook, headings, skimmable paragraphs, useful bullets, selective bold emphasis, and a concrete takeaway. Preserve factual grounding and cite supporting sources. After drafting, call validate_ship30_draft; if it fails and redraft_allowed is true, perform exactly one controlled redraft and validate it once more.""",
                requires_ship30_validation=True,
            )
        elif any(term in normalized for term in self._research_terms):
            plan = WorkflowPlan(
                WorkflowIntent.RESEARCH_SYNTHESIS,
                """Use search_transcripts to gather evidence for the question, considering more than one relevant passage when useful. Synthesize recurring themes, agreements, differences, and practical implications. Keep every transcript-grounded claim tied to returned source metadata and state when evidence is insufficient.""",
            )
        else:
            plan = WorkflowPlan(
                WorkflowIntent.GROUNDED_QA,
                """Use search_transcripts before answering. Answer only from relevant transcript evidence, include useful source references, and explicitly say when the available evidence is insufficient. Do not use conversation memory as factual transcript evidence.""",
            )
        logger.info("Workflow routed: intent=%s", plan.intent.value)
        return plan
