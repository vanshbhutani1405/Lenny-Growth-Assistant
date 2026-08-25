from dataclasses import dataclass

import pytest

from app.rag.generator import (
    INSUFFICIENT_CONTEXT_ANSWER,
    GenerationError,
    GroundedAnswerGenerator,
)
from app.rag.types import RetrievedChunk


def chunk(number: int = 1, *, score: float = 0.8) -> RetrievedChunk:
    return RetrievedChunk(
        id=f"chunk-{number}",
        episode_slug="growth-episode",
        chunk_text=f"Transcript evidence {number}",
        chunk_index=number,
        guest="Guest",
        title="Growth episode",
        youtube_url="https://youtube.example/video",
        relevance_score=score,
        semantic_score=score,
        retrieval_sources=("semantic",),
    )


@dataclass
class FakeRetriever:
    results: list[RetrievedChunk]

    def __post_init__(self) -> None:
        self.calls: list[dict] = []

    async def search(self, query: str, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return self.results


class FakeLLM:
    def __init__(self, answer: str = "Use [S1] to guide activation.") -> None:
        self.answer = answer
        self.calls: list[dict] = []

    async def generate(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.answer


@pytest.mark.asyncio
async def test_generates_grounded_answer_and_maps_sources() -> None:
    retriever = FakeRetriever([chunk(1), chunk(2, score=0.7)])
    llm = FakeLLM()

    result = await GroundedAnswerGenerator(retriever, llm).ask(
        "How do we improve activation?", top_k=2, episode="growth-episode", guest="Guest"
    )

    assert result.answer == "Use [S1] to guide activation."
    assert [source.chunk_id for source in result.sources] == ["chunk-1", "chunk-2"]
    assert result.sources[0].similarity_score == 0.8
    assert retriever.calls == [{
        "query": "How do we improve activation?",
        "top_k": 2,
        "filters": {"episode_slug": "growth-episode", "guest": "Guest"},
    }]
    assert "Transcript evidence 1" in llm.calls[0]["user_prompt"]


@pytest.mark.asyncio
async def test_empty_query_does_not_retrieve_or_generate() -> None:
    retriever = FakeRetriever([])
    llm = FakeLLM()

    result = await GroundedAnswerGenerator(retriever, llm).ask("  ")

    assert result.answer == "Please provide a question."
    assert result.sources == []
    assert retriever.calls == []
    assert llm.calls == []


@pytest.mark.asyncio
async def test_no_retrieved_context_returns_insufficient_answer() -> None:
    llm = FakeLLM()
    result = await GroundedAnswerGenerator(FakeRetriever([]), llm).ask("Unknown topic")

    assert result.answer == INSUFFICIENT_CONTEXT_ANSWER
    assert result.sources == []
    assert llm.calls == []


@pytest.mark.asyncio
async def test_context_is_bounded_by_chunk_count() -> None:
    retriever = FakeRetriever([chunk(i) for i in range(1, 5)])
    llm = FakeLLM()

    result = await GroundedAnswerGenerator(retriever, llm, max_context_chunks=2).ask("Question")

    assert len(result.sources) == 2
    assert "chunk_id=chunk-3" not in llm.calls[0]["user_prompt"]


@pytest.mark.asyncio
async def test_llm_failure_is_wrapped() -> None:
    class FailingLLM:
        async def generate(self, **kwargs) -> str:
            raise RuntimeError("provider failed")

    with pytest.raises(GenerationError, match="Unable to generate"):
        await GroundedAnswerGenerator(FakeRetriever([chunk()]), FailingLLM()).ask("Question")
