from datetime import date
from hashlib import sha256

from sqlalchemy import Date, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"
    __table_args__ = (
        Index("ix_transcript_chunks_episode_slug", "episode_slug"),
        Index("ix_transcript_chunks_episode_chunk_index", "episode_slug", "chunk_index", unique=True),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    episode_slug: Mapped[str] = mapped_column(String(255), index=True)
    guest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    # The embedding dimension is intentionally deferred until the model is selected.
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    @staticmethod
    def deterministic_id(episode_slug: str, chunk_index: int, chunk_text: str) -> str:
        identity = f"{episode_slug}\0{chunk_index}\0{chunk_text}".encode("utf-8")
        return sha256(identity).hexdigest()
