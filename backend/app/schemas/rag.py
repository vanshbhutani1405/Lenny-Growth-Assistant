from pydantic import BaseModel, Field


class RagAskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    episode: str | None = None
    guest: str | None = None


class RagSource(BaseModel):
    chunk_id: str
    episode_slug: str
    guest: str | None
    title: str | None
    chunk_index: int
    similarity_score: float
    youtube_url: str | None
    evidence: str | None = None


class RagAskResponse(BaseModel):
    answer: str
    sources: list[RagSource]
