import json
import logging
from dataclasses import asdict

from pydantic import BaseModel, Field, ValidationError

from app.rag.retriever import Retriever
from app.rag.types import RetrievedChunk

logger = logging.getLogger(__name__)


class TranscriptSearchArguments(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    episode: str | None = None
    guest: str | None = None


class TranscriptSearchTool:
    """Adapter between the Agent SDK tool protocol and the existing Retriever."""

    def __init__(self, retriever: Retriever, *, default_top_k: int | None = None) -> None:
        self.retriever = retriever
        self.default_top_k = default_top_k
        self.last_results: list[RetrievedChunk] = []

    async def search(self, arguments: dict) -> dict:
        logger.info("Agent transcript search tool invoked")
        try:
            parsed = TranscriptSearchArguments.model_validate(arguments)
        except ValidationError as exc:
            logger.warning("Invalid transcript search tool arguments")
            return self._text_result({"error": "invalid_arguments", "details": exc.errors()})

        try:
            self.last_results = await self.retriever.search(
                parsed.query,
                top_k=parsed.top_k if parsed.top_k is not None else self.default_top_k,
                filters={"episode_slug": parsed.episode, "guest": parsed.guest},
            )
        except Exception as exc:
            logger.exception("Agent transcript search tool failed")
            return self._text_result({"error": "retrieval_unavailable", "message": str(exc)})

        logger.info("Agent transcript search returned %d chunks", len(self.last_results))
        return self._text_result({"results": [self._serialize_result(item) for item in self.last_results]})

    @staticmethod
    def _serialize_result(chunk: RetrievedChunk) -> dict:
        return {
            "chunk_id": chunk.id,
            "episode_slug": chunk.episode_slug,
            "guest": chunk.guest,
            "title": chunk.title,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.chunk_text,
            "youtube_url": chunk.youtube_url,
            "similarity_score": chunk.relevance_score,
        }

    @staticmethod
    def _text_result(payload: dict) -> dict:
        return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}
