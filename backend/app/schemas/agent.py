from pydantic import BaseModel, Field

from app.schemas.rag import RagSource


class AgentAskRequest(BaseModel):
    session_id: str | None = Field(default=None, min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)


class AgentAskResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[RagSource]
