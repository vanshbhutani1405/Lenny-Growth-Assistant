from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class TranscriptDocument:
    episode_slug: str
    text: str
    guest: str | None = None
    title: str | None = None
    youtube_url: str | None = None
    publish_date: date | None = None
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    id: str
    episode_slug: str
    chunk_text: str
    chunk_index: int
    guest: str | None = None
    title: str | None = None
    youtube_url: str | None = None
    publish_date: date | None = None
    semantic_score: float | None = None
    keyword_score: float | None = None
    relevance_score: float = 0.0
    retrieval_sources: tuple[str, ...] = field(default_factory=tuple)
