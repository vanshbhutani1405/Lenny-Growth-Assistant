from datetime import date

from pydantic import BaseModel, Field


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=8, ge=1, le=50)
    episode_slug: str | None = None
    guest: str | None = None


class RetrievalResult(BaseModel):
    id: str
    episode_slug: str
    guest: str | None
    title: str | None
    youtube_url: str | None
    publish_date: date | None
    chunk_index: int
    chunk_text: str
    semantic_score: float | None
    keyword_score: float | None
    relevance_score: float
    retrieval_sources: list[str]


class RetrievalSearchResponse(BaseModel):
    query: str
    results: list[RetrievalResult]
    attempted_correction: bool
    corrective_query: str | None
