from types import SimpleNamespace
from urllib.error import URLError

import pytest

from app.agent.agent import LennyAgent
from app.providers.base import LLMProviderError
from app.providers.factory import select_local_provider
from app.providers.ollama import OllamaProvider
from app.rag.types import RetrievedChunk


def settings(provider: str = "ollama") -> SimpleNamespace:
    return SimpleNamespace(
        llm_provider=provider,
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        claude_model="claude-test",
    )


class FakeRetriever:
    async def search(self, query: str, **kwargs):
        return [RetrievedChunk(
            id="chunk-1",
            episode_slug="episode-1",
            chunk_text="Transcript evidence.",
            chunk_index=2,
            guest="Guest",
            title="Title",
            relevance_score=0.9,
        )]


class FakeOllama:
    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        assert "Transcript evidence." in user_prompt
        return "Grounded local answer [S1]."


def test_provider_selection() -> None:
    provider = select_local_provider(settings())
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "test-model"
    assert select_local_provider(settings("claude")) is None


@pytest.mark.asyncio
async def test_ollama_provider_posts_chat_request(monkeypatch) -> None:
    provider = OllamaProvider(base_url="http://localhost:11434/", model="test-model")
    captured = {}

    def fake_post(payload):
        captured["payload"] = payload
        return {"message": {"content": "local answer"}}

    monkeypatch.setattr(provider, "_post", fake_post)

    result = await provider.generate(system_prompt="system", user_prompt="user")

    assert result == "local answer"
    assert captured["payload"]["model"] == "test-model"
    assert captured["payload"]["stream"] is False


@pytest.mark.asyncio
async def test_ollama_provider_failure_is_wrapped(monkeypatch) -> None:
    provider = OllamaProvider(base_url="http://localhost:11434", model="test-model")
    monkeypatch.setattr(provider, "_post", lambda payload: (_ for _ in ()).throw(URLError("offline")))

    with pytest.raises(LLMProviderError, match="Ollama request failed"):
        await provider.generate(system_prompt="system", user_prompt="user")


@pytest.mark.asyncio
async def test_ollama_agent_preserves_grounded_sources() -> None:
    result = await LennyAgent(
        FakeRetriever(),
        settings(),
        local_provider=FakeOllama(),
    ).ask("What does the transcript say?")

    assert result.answer == "Grounded local answer [S1]."
    assert result.sources[0].chunk_id == "chunk-1"
    assert result.sources[0].episode_slug == "episode-1"
