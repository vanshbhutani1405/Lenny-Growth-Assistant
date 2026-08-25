from types import SimpleNamespace

import pytest

from app.agent.agent import AgentAnswer, LennyAgent
from app.agent.tools import TranscriptSearchTool
from app.rag.types import RetrievedChunk


def evidence() -> RetrievedChunk:
    return RetrievedChunk(
        id="chunk-1",
        episode_slug="growth-episode",
        chunk_text="Evidence about activation.",
        chunk_index=4,
        guest="Guest",
        title="Growth episode",
        youtube_url="https://youtube.example/video",
        relevance_score=0.82,
        semantic_score=0.82,
        retrieval_sources=("semantic",),
    )


class FakeRetriever:
    def __init__(self, results=None) -> None:
        self.results = results if results is not None else [evidence()]
        self.calls = []

    async def search(self, query: str, **kwargs):
        self.calls.append((query, kwargs))
        return self.results


@pytest.mark.asyncio
async def test_transcript_tool_preserves_evidence_metadata_and_filters() -> None:
    retriever = FakeRetriever()
    tool = TranscriptSearchTool(retriever)

    result = await tool.search({
        "query": "activation",
        "top_k": 3,
        "episode": "growth-episode",
        "guest": "Guest",
    })

    assert retriever.calls == [(
        "activation",
        {"top_k": 3, "filters": {"episode_slug": "growth-episode", "guest": "Guest"}},
    )]
    assert '"chunk_id": "chunk-1"' in result["content"][0]["text"]
    assert '"chunk_index": 4' in result["content"][0]["text"]
    assert '"similarity_score": 0.82' in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_transcript_tool_validates_arguments() -> None:
    retriever = FakeRetriever()
    result = await TranscriptSearchTool(retriever).search({"query": ""})

    assert '"error": "invalid_arguments"' in result["content"][0]["text"]
    assert retriever.calls == []


@pytest.mark.asyncio
async def test_agent_invokes_sdk_workflow_and_returns_sources(monkeypatch) -> None:
    retriever = FakeRetriever()
    captured = {}

    class FakeClient:
        def __init__(self, *, options) -> None:
            captured["options"] = options

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def query(self, prompt: str) -> None:
            captured["prompt"] = prompt
            await captured["sdk_tool"]({"query": "activation", "top_k": 2})

        async def receive_response(self):
            yield "fake-message"

    def fake_tool(name, description, schema):
        def decorator(function):
            captured["sdk_tool"] = function
            return function
        return decorator

    class FakeOptions:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    def fake_server_factory(**kwargs):
        captured["server"] = kwargs
        return "fake-server"

    agent = LennyAgent(
        retriever,
        SimpleNamespace(claude_model="claude-test"),
    )
    monkeypatch.setattr(
        LennyAgent,
        "_sdk_api",
        staticmethod(lambda: (FakeClient, fake_tool, fake_server_factory, FakeOptions)),
    )
    monkeypatch.setattr(
        LennyAgent,
        "_text_blocks",
        staticmethod(lambda message: ["Grounded answer [chunk-1]."]),
    )

    result = await agent.ask("How do we improve activation?", top_k=2)

    assert result.answer == "Grounded answer [chunk-1]."
    assert result.sources[0].chunk_id == "chunk-1"
    assert retriever.calls[0][1]["top_k"] == 2
    assert captured["options"].kwargs["allowed_tools"] == ["mcp__lenny__search_transcripts"]
    assert "search_transcripts" in captured["prompt"]


@pytest.mark.asyncio
async def test_agent_returns_insufficient_evidence_response_without_sources(monkeypatch) -> None:
    retriever = FakeRetriever(results=[])

    class FakeClient:
        def __init__(self, *, options) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def query(self, prompt: str) -> None:
            await captured_tool({"query": "unsupported"})

        async def receive_response(self):
            yield "fake-message"

    captured_tool = None

    def fake_tool(name, description, schema):
        def decorator(function):
            nonlocal captured_tool
            captured_tool = function
            return function
        return decorator

    class FakeOptions:
        def __init__(self, **kwargs) -> None:
            pass

    agent = LennyAgent(retriever, SimpleNamespace(claude_model="claude-test"))
    monkeypatch.setattr(
        LennyAgent,
        "_sdk_api",
        staticmethod(lambda: (FakeClient, fake_tool, lambda **kwargs: "server", FakeOptions)),
    )
    monkeypatch.setattr(
        LennyAgent,
        "_text_blocks",
        staticmethod(lambda message: [
            "The available transcript evidence is insufficient to answer reliably."
        ]),
    )

    result = await agent.ask("Unsupported question")

    assert isinstance(result, AgentAnswer)
    assert "insufficient" in result.answer
    assert result.sources == []
