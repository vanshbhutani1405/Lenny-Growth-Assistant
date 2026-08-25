import pytest
from httpx import ASGITransport, AsyncClient

from app.rag.types import RetrievedChunk


@pytest.mark.asyncio
async def test_retrieval_api_returns_inspectable_scores_and_metadata(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from app.api.v1 import retrieval as retrieval_api
    from app.database.session import get_db_session
    from app.main import create_app
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    class FakeRetriever:
        def __init__(self, session):
            pass

        async def search(self, *, query, top_k, filters):
            return [RetrievedChunk(
                    "id-1", "episode-1", "evidence", 2,
                    guest="Guest", title="Title", youtube_url="https://example.com",
                    semantic_score=0.9, relevance_score=0.9,
                    retrieval_sources=("semantic",),
                )]

    retrieval_api.Retriever = FakeRetriever
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override():
        async with factory() as session:
            yield session

    application = create_app()
    application.dependency_overrides[get_db_session] = override
    async with AsyncClient(transport=ASGITransport(app=application), base_url="http://test") as client:
        response = await client.post("/api/v1/retrieval/search", json={"query": "activation strategy"})
    await engine.dispose()
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["retrieval_sources"] == ["semantic"]
    assert result["youtube_url"] == "https://example.com"
