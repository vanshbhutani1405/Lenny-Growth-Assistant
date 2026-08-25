import logging
from dataclasses import dataclass
from typing import Protocol

from app.rag.retriever import Retriever
from app.rag.types import RetrievedChunk

logger = logging.getLogger(__name__)

INSUFFICIENT_CONTEXT_ANSWER = (
    "The available transcripts do not contain enough information to answer this question reliably."
)


class GenerationError(RuntimeError):
    """Raised when a grounded answer cannot be generated."""


class LLMClient(Protocol):
    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate text from the supplied bounded prompt."""


class UnavailableLLMClient:
    """Explicit default until a project LLM provider is configured."""

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise GenerationError("No LLM provider is configured for grounded answer generation")


@dataclass(frozen=True, slots=True)
class SourceCitation:
    chunk_id: str
    episode_slug: str
    guest: str | None
    title: str | None
    chunk_index: int
    similarity_score: float
    youtube_url: str | None = None
    evidence: str | None = None


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    answer: str
    sources: list[SourceCitation]


class GroundedAnswerGenerator:
    """Retrieve bounded transcript evidence and ask an LLM to cite only that evidence."""

    def __init__(
        self,
        retriever: Retriever,
        llm_client: LLMClient,
        *,
        max_context_chunks: int = 5,
        max_context_chars: int = 12_000,
    ) -> None:
        self.retriever = retriever
        self.llm_client = llm_client
        self.max_context_chunks = max_context_chunks
        self.max_context_chars = max_context_chars

    async def ask(
        self,
        query: str,
        *,
        top_k: int | None = None,
        episode: str | None = None,
        guest: str | None = None,
    ) -> GroundedAnswer:
        normalized_query = query.strip()
        if not normalized_query:
            return GroundedAnswer("Please provide a question.", [])

        try:
            retrieved = await self.retriever.search(
                normalized_query,
                top_k=top_k,
                filters={"episode_slug": episode, "guest": guest},
            )
        except Exception as exc:
            logger.exception("Grounded answer retrieval failed")
            raise GenerationError("Unable to retrieve transcript context") from exc

        logger.info("Grounded answer retrieval complete: count=%d", len(retrieved))
        if not retrieved:
            return GroundedAnswer(INSUFFICIENT_CONTEXT_ANSWER, [])

        context, context_chunks = self._build_context(retrieved)
        logger.info(
            "Grounded answer context built: chunks=%d chars=%d",
            len(context_chunks),
            len(context),
        )
        if not context_chunks:
            return GroundedAnswer(INSUFFICIENT_CONTEXT_ANSWER, [])

        system_prompt = (
            "You answer questions using only the supplied transcript excerpts. "
            "Do not use outside knowledge or invent facts. If the excerpts do not "
            "support an answer, say that the available transcripts do not contain "
            "enough information. Cite supporting excerpts inline as [S1], [S2], etc."
        )
        user_prompt = f"Question:\n{normalized_query}\n\nTranscript excerpts:\n{context}"

        logger.info("Grounded answer generation started")
        try:
            answer = (await self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )).strip()
        except Exception as exc:
            logger.exception("Grounded answer generation failed")
            raise GenerationError("Unable to generate grounded answer") from exc
        logger.info("Grounded answer generation completed")

        if not answer:
            raise GenerationError("LLM returned an empty grounded answer")
        return GroundedAnswer(answer, [self._source_for(chunk) for chunk in context_chunks])

    def _build_context(self, chunks: list[RetrievedChunk]) -> tuple[str, list[RetrievedChunk]]:
        blocks: list[str] = []
        selected: list[RetrievedChunk] = []
        total_chars = 0
        for source_number, chunk in enumerate(chunks[: self.max_context_chunks], start=1):
            metadata = (
                f"[S{source_number}] episode={chunk.episode_slug}; "
                f"guest={chunk.guest or 'unknown'}; title={chunk.title or 'unknown'}; "
                f"similarity={chunk.relevance_score:.4f}; chunk_id={chunk.id}"
            )
            block = f"{metadata}\n{chunk.chunk_text}"
            separator_chars = 2 if blocks else 0
            available = self.max_context_chars - total_chars - separator_chars
            if available <= 0:
                break
            if len(block) > available:
                block = block[:available].rstrip()
            blocks.append(block)
            selected.append(chunk)
            total_chars += separator_chars + len(block)
            if len(block) < len(metadata) + len(chunk.chunk_text):
                break
        return "\n\n".join(blocks), selected

    @staticmethod
    def _source_for(chunk: RetrievedChunk) -> SourceCitation:
        return SourceCitation(
            chunk_id=chunk.id,
            episode_slug=chunk.episode_slug,
            guest=chunk.guest,
            title=chunk.title,
            chunk_index=chunk.chunk_index,
            similarity_score=chunk.relevance_score,
            youtube_url=chunk.youtube_url,
            evidence=chunk.chunk_text,
        )
