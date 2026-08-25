from types import SimpleNamespace

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.transcript_chunk import TranscriptChunk
from app.rag.retriever import RetrievalError, Retriever


class FakeEmbeddingService:
    def __init__(self):
        self.queries = []

    def embed_query(self, query):
        self.queries.append(query)
        return [0.1, 0.2, 0.3]


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        limit = statement._limit_clause.value
        return FakeResult(self.rows[:limit])


def make_chunk(chunk_id: str, index: int) -> TranscriptChunk:
    return TranscriptChunk(
        id=chunk_id,
        episode_slug="episode-1",
        guest="Guest",
        title="Title",
        chunk_index=index,
        chunk_text=f"Evidence {index}",
    )


def make_retriever(session, embedding=None, *, top_k=2, min_score=0.5):
    return Retriever(
        session,
        embedding_service=embedding or FakeEmbeddingService(),
        settings=SimpleNamespace(retrieval_top_k=top_k, retrieval_min_score=min_score),
    )


@pytest.mark.asyncio
async def test_retriever_embeds_query_and_maps_metadata():
    embedding = FakeEmbeddingService()
    session = FakeSession([(make_chunk("a", 0), 0.91)])

    results = await make_retriever(session, embedding).search("activation strategy")

    assert embedding.queries == ["activation strategy"]
    assert results[0].episode_slug == "episode-1"
    assert results[0].guest == "Guest"
    assert results[0].title == "Title"
    assert results[0].chunk_index == 0
    assert results[0].chunk_text == "Evidence 0"
    assert results[0].relevance_score == pytest.approx(0.91)


@pytest.mark.asyncio
async def test_retriever_applies_top_k_and_minimum_score_in_sql():
    session = FakeSession([(make_chunk("a", 0), 0.91), (make_chunk("b", 1), 0.80), (make_chunk("c", 2), 0.55)])

    results = await make_retriever(session, top_k=2, min_score=0.75).search("growth")

    assert [result.id for result in results] == ["a", "b"]
    sql = str(session.statements[0])
    assert "LIMIT" in sql.upper()
    assert ">=" in sql


@pytest.mark.asyncio
async def test_retriever_returns_empty_for_empty_query_and_no_results():
    embedding = FakeEmbeddingService()
    empty_session = FakeSession([])
    retriever = make_retriever(empty_session, embedding)

    assert await retriever.search("   ") == []
    assert embedding.queries == []
    assert await retriever.search("unsupported question") == []


@pytest.mark.asyncio
async def test_retriever_wraps_embedding_and_database_errors():
    class FailingEmbedding:
        def embed_query(self, query):
            raise ValueError("embedding failed")

    with pytest.raises(RetrievalError, match="embed"):
        await make_retriever(FakeSession([]), FailingEmbedding()).search("query")

    class FailingSession(FakeSession):
        async def execute(self, statement):
            raise SQLAlchemyError("database failed")

    with pytest.raises(RetrievalError, match="retrieve"):
        await make_retriever(FailingSession([])).search("query")
