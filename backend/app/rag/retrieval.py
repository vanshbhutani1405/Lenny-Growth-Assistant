from dataclasses import dataclass

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript_chunk import TranscriptChunk
from app.rag.embeddings import EmbeddingService, get_embedding_service
from app.rag.ranking import combine_results
from app.rag.types import RetrievedChunk


@dataclass(frozen=True, slots=True)
class RetrievalResponse:
    results: list[RetrievedChunk]
    attempted_correction: bool = False
    corrective_query: str | None = None


def rewrite_query(query: str) -> str:
    terms = [term for term in query.strip().split() if len(term) > 2]
    return "product growth " + " ".join(terms[:12])


class RetrievalService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        embedding_service: EmbeddingService | None = None,
        semantic_weight: float = 0.65,
        keyword_weight: float = 0.35,
        min_relevance: float = 0.18,
    ) -> None:
        self.session = session
        self.embedding_service = embedding_service or get_embedding_service()
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.min_relevance = min_relevance

    def _filters(self, filters: dict[str, str] | None) -> list:
        filters = filters or {}
        clauses = []
        if filters.get("episode_slug"):
            clauses.append(TranscriptChunk.episode_slug == filters["episode_slug"])
        if filters.get("guest"):
            clauses.append(TranscriptChunk.guest == filters["guest"])
        return clauses

    async def semantic_search(self, query: str, top_k: int, filters: dict[str, str] | None = None) -> list[RetrievedChunk]:
        vector = self.embedding_service.embed_query(query)
        distance = TranscriptChunk.embedding.cosine_distance(vector)
        statement = select(TranscriptChunk, distance.label("distance")).where(
            TranscriptChunk.embedding.is_not(None)
        ).where(*self._filters(filters)).order_by(distance).limit(top_k)
        rows = (await self.session.execute(statement)).all()
        return [self._row_to_result(chunk, semantic_score=max(0.0, 1.0 - float(distance_value))) for chunk, distance_value in rows]

    async def keyword_search(self, query: str, top_k: int, filters: dict[str, str] | None = None) -> list[RetrievedChunk]:
        vector = func.to_tsvector("english", func.coalesce(TranscriptChunk.chunk_text, ""))
        terms = func.plainto_tsquery("english", query)
        score = func.ts_rank_cd(vector, terms)
        statement = select(TranscriptChunk, score.label("score")).where(vector.op("@@")(terms), *self._filters(filters)).order_by(desc(score)).limit(top_k)
        rows = (await self.session.execute(statement)).all()
        maximum = max((float(score_value) for _, score_value in rows), default=0.0)
        return [
            self._row_to_result(
                chunk,
                keyword_score=(float(score_value) / maximum if maximum else 0.0),
            )
            for chunk, score_value in rows
        ]

    async def _retrieve_once(self, query: str, top_k: int, filters: dict[str, str] | None = None) -> list[RetrievedChunk]:
        semantic, keyword = await self._parallel_retrieve(query, top_k, filters)
        return combine_results(semantic, keyword, semantic_weight=self.semantic_weight, keyword_weight=self.keyword_weight)[:top_k]

    async def _parallel_retrieve(self, query: str, top_k: int, filters: dict[str, str] | None = None) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
        # Kept sequential so one database session is never concurrently used by two tasks.
        return await self.semantic_search(query, top_k, filters), await self.keyword_search(query, top_k, filters)

    async def search(self, query: str, top_k: int = 8, filters: dict[str, str] | None = None) -> RetrievalResponse:
        first = await self._retrieve_once(query, top_k, filters)
        if first and first[0].relevance_score >= self.min_relevance:
            return RetrievalResponse(first)
        corrected = rewrite_query(query)
        if corrected == query.strip():
            return RetrievalResponse(first)
        second = await self._retrieve_once(corrected, top_k, filters)
        return RetrievalResponse(
            second if second and second[0].relevance_score > (first[0].relevance_score if first else 0.0) else first,
            attempted_correction=True,
            corrective_query=corrected,
        )

    @staticmethod
    def _row_to_result(
        chunk: TranscriptChunk,
        *,
        semantic_score: float | None = None,
        keyword_score: float | None = None,
    ) -> RetrievedChunk:
        return RetrievedChunk(
            id=chunk.id,
            episode_slug=chunk.episode_slug,
            chunk_text=chunk.chunk_text,
            chunk_index=chunk.chunk_index,
            guest=chunk.guest,
            title=chunk.title,
            youtube_url=chunk.youtube_url,
            publish_date=chunk.publish_date,
            semantic_score=semantic_score,
            keyword_score=keyword_score,
        )
