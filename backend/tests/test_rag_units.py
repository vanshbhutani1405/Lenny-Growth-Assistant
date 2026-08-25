from datetime import date
import logging
from pathlib import Path

import pytest
from sqlalchemy.dialects.postgresql import dialect as postgres_dialect
from sqlalchemy.exc import SQLAlchemyError

from app.models.transcript_chunk import TranscriptChunk
from app.rag.chunking import chunk_transcript
from app.rag.embeddings import EmbeddingService
from app.rag.ingestion import ingest_corpus
from app.rag.loaders import load_corpus
from app.rag.normalization import normalize_transcript_text
from app.rag.ranking import combine_results
from app.rag.retrieval import RetrievalResponse, RetrievalService
from app.rag.types import RetrievedChunk


def test_normalization_preserves_words_and_paragraphs():
    assert normalize_transcript_text(" A\r\n\r\n  useful\u00a0 idea \t here ") == "A\n\nuseful idea here"


def test_chunking_is_overlapping_and_deterministic():
    text = " ".join(f"word{i}" for i in range(125))
    chunks = chunk_transcript(text, chunk_size_words=50, overlap_words=10)
    assert chunks == chunk_transcript(text, chunk_size_words=50, overlap_words=10)
    assert chunks[0].text.split()[-10:] == chunks[1].text.split()[:10]
    assert len(chunks[-1].text.split()) >= 20


def test_deterministic_chunk_id_changes_with_content():
    first = TranscriptChunk.deterministic_id("episode", 0, "same")
    assert first == TranscriptChunk.deterministic_id("episode", 0, "same")
    assert first != TranscriptChunk.deterministic_id("episode", 1, "same")


def test_loader_preserves_json_metadata(tmp_path: Path):
    path = tmp_path / "episode.json"
    path.write_text(
        '{"episode_slug":"ep-1","guest":"Guest","title":"Title",'
        '"youtube_url":"https://youtu.be/x","publish_date":"2024-01-02",'
        '"transcript":"A useful transcript."}',
        encoding="utf-8",
    )
    document = load_corpus(path)[0]
    assert (document.episode_slug, document.guest, document.title, document.publish_date) == (
        "ep-1",
        "Guest",
        "Title",
        date(2024, 1, 2),
    )
    assert document.youtube_url == "https://youtu.be/x"


def test_markdown_loader_uses_parent_episode_slug(tmp_path: Path):
    episode_dir = tmp_path / "ada-chen-rekhi"
    episode_dir.mkdir()
    path = episode_dir / "transcript.md"
    path.write_text("---\nguest: Ada Chen Rekhi\n---\n\n## Transcript\nUseful advice.", encoding="utf-8")

    document = load_corpus(episode_dir)[0]

    assert document.episode_slug == "ada-chen-rekhi"


def test_embedding_service_reuses_model_and_validates_shape():
    class FakeModel:
        calls = 0

        def get_embedding_dimension(self):
            return 3

        def encode(self, texts, **kwargs):
            self.calls += 1
            return [[1, 0, 0] for _ in texts]

    service = EmbeddingService("fake", 3)
    service._model = FakeModel()
    assert service.embed(["one", "two"]) == [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    assert service.embed(["three"]) == [[1.0, 0.0, 0.0]]
    assert service._model.calls == 2


def test_hybrid_ranking_is_explainable_and_deterministic():
    semantic = [RetrievedChunk("a", "ep", "semantic", 0, semantic_score=0.9)]
    keyword = [RetrievedChunk("a", "ep", "keyword", 0, keyword_score=0.5), RetrievedChunk("b", "ep", "exact", 1, keyword_score=0.8)]
    results = combine_results(semantic, keyword)
    assert results[0].id == "a"
    assert results[0].retrieval_sources == ("semantic", "keyword")
    assert results[0].relevance_score == pytest.approx(0.9 * 0.65 + 0.5 * 0.35)


def test_persistence_statement_is_postgres_upsert():
    chunk = TranscriptChunk(
        id="chunk-1",
        episode_slug="episode",
        chunk_index=0,
        chunk_text="text",
        embedding=[0.1, 0.2, 0.3],
    )
    from app.rag.ingestion import postgres_insert

    statement = postgres_insert(TranscriptChunk).values(
        {
            "id": chunk.id,
            "episode_slug": chunk.episode_slug,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.chunk_text,
            "embedding": chunk.embedding,
        }
    ).on_conflict_do_update(
        index_elements=[TranscriptChunk.id],
        set_={"chunk_text": chunk.chunk_text},
    )
    sql = str(statement.compile(dialect=postgres_dialect()))
    assert "ON CONFLICT (id) DO UPDATE" in sql


@pytest.mark.asyncio
async def test_ingestion_is_idempotent_with_deterministic_upsert(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    caplog.set_level(logging.INFO, logger="app.rag.ingestion")
    corpus = tmp_path / "episode.json"
    corpus.write_text('{"episode":"ep","text":""' + '"}', encoding="utf-8")
    corpus.write_text('{"episode":"ep","guest":"G","text":"' + "useful " * 40 + '"}', encoding="utf-8")

    class FakeEmbedding:
        def embed(self, texts):
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FakeSession:
        def __init__(self):
            self.executed = []
            self.commit_calls = 0
            self.rollback_calls = 0

        async def execute(self, statement):
            self.executed.append(statement)

        async def commit(self):
            self.commit_calls += 1

        async def rollback(self):
            self.rollback_calls += 1

    session = FakeSession()
    first = await ingest_corpus(session, corpus, embedding_service=FakeEmbedding(), chunk_size_words=30, overlap_words=5)
    second = await ingest_corpus(session, corpus, embedding_service=FakeEmbedding(), chunk_size_words=30, overlap_words=5)
    assert first.chunks == second.chunks == 1
    assert len(session.executed) == 2
    assert session.commit_calls == 2
    assert session.rollback_calls == 0
    assert any("Processing document 1/1" in record.message for record in caplog.records)
    assert any("Persisted batch 1" in record.message for record in caplog.records)
    assert any("Ingestion complete" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_ingestion_rolls_back_failed_batch(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    corpus = tmp_path / "episode.json"
    corpus.write_text('{"episode":"ep","text":"useful useful useful"}', encoding="utf-8")

    class FakeEmbedding:
        def embed(self, texts):
            return [[0.1, 0.2, 0.3] for _ in texts]

    class FailingSession:
        rollback_calls = 0

        async def execute(self, statement):
            raise SQLAlchemyError("write failed")

        async def commit(self):
            raise AssertionError("commit should not be reached")

        async def rollback(self):
            self.rollback_calls += 1

    session = FailingSession()
    with pytest.raises(SQLAlchemyError):
        await ingest_corpus(session, corpus, embedding_service=FakeEmbedding(), chunk_size_words=30, overlap_words=5)
    assert session.rollback_calls == 1


class StubRetrievalService(RetrievalService):
    def __init__(self):
        pass

    async def _retrieve_once(self, query, top_k, filters=None):
        if query.startswith("product growth"):
            return [RetrievedChunk("corrected", "ep", "strong evidence", 0, relevance_score=0.8)]
        return []


@pytest.mark.asyncio
async def test_corrective_retrieval_attempts_exactly_once():
    result = await StubRetrievalService().search("obscure question", top_k=3)
    assert isinstance(result, RetrievalResponse)
    assert result.attempted_correction is True
    assert result.corrective_query is not None
    assert [item.id for item in result.results] == ["corrected"]
