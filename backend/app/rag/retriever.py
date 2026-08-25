import logging
from dataclasses import dataclass

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.transcript_chunk import TranscriptChunk
from app.rag.embeddings import EmbeddingService, get_embedding_service
from app.rag.types import RetrievedChunk
from app.observability.tracing import traced

logger = logging.getLogger(__name__)


class RetrievalError(RuntimeError):
    """Raised when query embedding or database retrieval fails."""


@dataclass(frozen=True, slots=True)
class Retriever:
    session: AsyncSession
    embedding_service: EmbeddingService
    settings: Settings

    def __init__(
        self,
        session: AsyncSession,
        *,
        embedding_service: EmbeddingService | None = None,
        settings: Settings | None = None,
    ) -> None:
        object.__setattr__(self, "session", session)
        object.__setattr__(self, "embedding_service", embedding_service or get_embedding_service())
        object.__setattr__(self, "settings", settings or get_settings())

    @traced("rag.retriever.search", run_type="retriever")
    async def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        min_score: float | None = None,
        filters: dict[str, str | None] | None = None,
    ) -> list[RetrievedChunk]:
        normalized_query = query.strip()
        if not normalized_query:
            logger.info("Retrieval query was empty; returning no chunks")
            return []

        result_limit = top_k if top_k is not None else self.settings.retrieval_top_k
        score_floor = min_score if min_score is not None else self.settings.retrieval_min_score
        if result_limit <= 0:
            raise ValueError("top_k must be positive")

        logger.info("Retrieval query received: query_length=%d top_k=%d", len(normalized_query), result_limit)
        try:
            query_embedding = self.embedding_service.embed_query(normalized_query)
        except Exception as exc:
            logger.exception("Failed to embed retrieval query")
            raise RetrievalError("Unable to embed retrieval query") from exc

        distance = TranscriptChunk.embedding.cosine_distance(query_embedding)
        similarity = (1 - distance).label("similarity")
        statement = (
            select(TranscriptChunk, similarity)
            .where(
                TranscriptChunk.embedding.is_not(None),
                similarity >= score_floor,
                *self._filter_clauses(filters),
            )
            .order_by(desc(similarity), TranscriptChunk.id)
            .limit(result_limit)
        )

        try:
            rows = (await self.session.execute(statement)).all()
        except SQLAlchemyError as exc:
            logger.exception("Failed to retrieve transcript chunks")
            raise RetrievalError("Unable to retrieve transcript chunks") from exc

        results = [self._map_row(chunk, score) for chunk, score in rows]
        logger.info(
            "Retrieved transcript chunks: count=%d top_similarity=%s",
            len(results),
            f"{results[0].relevance_score:.4f}" if results else "none",
        )
        return results

    @staticmethod
    def _filter_clauses(filters: dict[str, str | None] | None) -> list:
        filters = filters or {}
        clauses = []
        if filters.get("episode_slug"):
            clauses.append(TranscriptChunk.episode_slug == filters["episode_slug"])
        if filters.get("guest"):
            clauses.append(TranscriptChunk.guest == filters["guest"])
        return clauses

    @staticmethod
    def _map_row(chunk: TranscriptChunk, score: float) -> RetrievedChunk:
        similarity = float(score)
        return RetrievedChunk(
            id=chunk.id,
            episode_slug=chunk.episode_slug,
            chunk_text=chunk.chunk_text,
            chunk_index=chunk.chunk_index,
            guest=chunk.guest,
            title=chunk.title,
            youtube_url=chunk.youtube_url,
            publish_date=chunk.publish_date,
            semantic_score=similarity,
            relevance_score=similarity,
            retrieval_sources=("semantic",),
        )
