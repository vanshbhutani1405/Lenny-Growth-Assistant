from app.models import Message, Session, TranscriptChunk


def test_core_models_have_expected_tables_and_constraints():
    assert {Session.__tablename__, Message.__tablename__, TranscriptChunk.__tablename__} == {"sessions", "messages", "transcript_chunks"}
    assert "session_id" in Message.__table__.c
    assert "embedding" in TranscriptChunk.__table__.c
    assert any(index.unique for index in TranscriptChunk.__table__.indexes)
    assert TranscriptChunk.deterministic_id("episode", 0, "text") == TranscriptChunk.deterministic_id("episode", 0, "text")
