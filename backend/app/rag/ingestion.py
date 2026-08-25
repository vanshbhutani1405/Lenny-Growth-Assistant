from dataclasses import dataclass
import logging
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.transcript_chunk import TranscriptChunk
from app.rag.chunking import chunk_transcript
from app.rag.embeddings import EmbeddingService, get_embedding_service
from app.rag.loaders import load_corpus

logger = logging.getLogger(__name__)
DEFAULT_INGESTION_BATCH_SIZE = 100


@dataclass(frozen=True, slots=True)
class IngestionStats:
    documents: int
    chunks: int
    inserted_or_updated: int


async def ingest_corpus(
    session: AsyncSession,
    corpus_path: Path,
    *,
    embedding_service: EmbeddingService | None = None,
    chunk_size_words: int | None = None,
    overlap_words: int | None = None,
    batch_size: int = DEFAULT_INGESTION_BATCH_SIZE,
) -> IngestionStats:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    settings = get_settings()
    service = embedding_service or get_embedding_service()
    documents = load_corpus(corpus_path)
    chunk_size = chunk_size_words or settings.chunk_size_words
    overlap = overlap_words if overlap_words is not None else settings.chunk_overlap_words
    pending: list[TranscriptChunk] = []
    total_chunks = 0
    persisted_chunks = 0

    logger.info("Starting ingestion: documents=%d batch_size=%d", len(documents), batch_size)
    for document_index, document in enumerate(documents, start=1):
        chunks = chunk_transcript(document.text, chunk_size_words=chunk_size, overlap_words=overlap)
        logger.info(
            "Embedding document %d/%d: episode=%s chunks=%d",
            document_index,
            len(documents),
            document.episode_slug,
            len(chunks),
        )
        vectors = service.embed([chunk.text for chunk in chunks])
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk_id = TranscriptChunk.deterministic_id(document.episode_slug, chunk.index, chunk.text)
            pending.append(
                TranscriptChunk(
                    id=chunk_id,
                    episode_slug=document.episode_slug,
                    guest=document.guest,
                    title=document.title,
                    youtube_url=document.youtube_url,
                    publish_date=document.publish_date,
                    chunk_index=chunk.index,
                    chunk_text=chunk.text,
                    embedding=vector,
                )
            )
            total_chunks += 1
            if len(pending) >= batch_size:
                await _persist_batch(session, pending)
                persisted_chunks += len(pending)
                logger.info("Committed ingestion batch: chunks=%d", persisted_chunks)
                pending.clear()

    if pending:
        await _persist_batch(session, pending)
        persisted_chunks += len(pending)
        logger.info("Committed final ingestion batch: chunks=%d", persisted_chunks)

    logger.info("Ingestion complete: documents=%d chunks=%d", len(documents), total_chunks)
    return IngestionStats(len(documents), total_chunks, persisted_chunks)


async def _persist_batch(session: AsyncSession, chunks: list[TranscriptChunk]) -> None:
    values = [
        {
            "id": chunk.id,
            "episode_slug": chunk.episode_slug,
            "guest": chunk.guest,
            "title": chunk.title,
            "youtube_url": chunk.youtube_url,
            "publish_date": chunk.publish_date,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.chunk_text,
            "embedding": chunk.embedding,
        }
        for chunk in chunks
    ]
    statement = postgres_insert(TranscriptChunk).values(values)
    statement = statement.on_conflict_do_update(
        index_elements=[TranscriptChunk.id],
        set_={
            "episode_slug": statement.excluded.episode_slug,
            "guest": statement.excluded.guest,
            "title": statement.excluded.title,
            "youtube_url": statement.excluded.youtube_url,
            "publish_date": statement.excluded.publish_date,
            "chunk_index": statement.excluded.chunk_index,
            "chunk_text": statement.excluded.chunk_text,
            "embedding": statement.excluded.embedding,
        },
    )
    try:
        await session.execute(statement)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        logger.exception("Failed to persist ingestion batch of %d chunks", len(chunks))
        raise
