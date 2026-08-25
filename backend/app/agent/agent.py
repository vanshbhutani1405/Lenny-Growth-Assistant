import logging
from dataclasses import dataclass
from typing import Any

from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.tools import TranscriptSearchTool
from app.core.config import Settings
from app.rag.retriever import Retriever
from app.rag.generator import SourceCitation
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.factory import select_local_provider

logger = logging.getLogger(__name__)


class AgentError(RuntimeError):
    """Raised when the Claude Agent SDK workflow cannot complete."""


class AgentConfigurationError(AgentError):
    """Raised when Claude configuration or the SDK is unavailable."""


@dataclass(frozen=True, slots=True)
class AgentAnswer:
    answer: str
    sources: list[SourceCitation]


class LennyAgent:
    def __init__(
        self,
        retriever: Retriever,
        settings: Settings,
        *,
        local_provider: LLMProvider | None = None,
    ) -> None:
        self.retriever = retriever
        self.settings = settings
        self.local_provider = local_provider if local_provider is not None else select_local_provider(settings)

    async def ask(self, query: str, *, top_k: int | None = None) -> AgentAnswer:
        normalized_query = query.strip()
        if not normalized_query:
            raise AgentError("query must not be empty")

        logger.info("Agent request received: query_length=%d", len(normalized_query))
        search_tool = TranscriptSearchTool(self.retriever, default_top_k=top_k)
        provider = getattr(self.settings, "llm_provider", "claude").strip().lower()
        if provider == "ollama":
            return await self._ask_ollama(normalized_query, search_tool)
        if provider != "claude":
            raise AgentConfigurationError(f"Unsupported LLM_PROVIDER: {self.settings.llm_provider}")
        return await self._ask_claude(normalized_query, top_k, search_tool)

    async def _ask_claude(
        self,
        query: str,
        top_k: int | None,
        search_tool: TranscriptSearchTool,
    ) -> AgentAnswer:
        try:
            client_class, tool_decorator, server_factory, options_class = self._sdk_api()
            sdk_tool = self._make_sdk_tool(tool_decorator, search_tool)
            server = server_factory(name="lenny-transcripts", tools=[sdk_tool])
            options = options_class(
                model=self.settings.claude_model,
                system_prompt=AGENT_SYSTEM_PROMPT,
                max_turns=3,
                mcp_servers={"lenny": server},
                allowed_tools=["mcp__lenny__search_transcripts"],
            )

            logger.info("Claude generation started: model=%s", self.settings.claude_model)
            answer_parts: list[str] = []
            async with client_class(options=options) as client:
                await client.query(self._build_prompt(query, top_k))
                async for message in client.receive_response():
                    answer_parts.extend(self._text_blocks(message))
            answer = "\n".join(part for part in answer_parts if part).strip()
            if not answer:
                raise AgentError("Claude returned an empty answer")
            logger.info("Claude generation completed: sources=%d", len(search_tool.last_results))
            return AgentAnswer(answer, [self._source_for(chunk) for chunk in search_tool.last_results])
        except AgentError:
            raise
        except Exception as exc:
            logger.exception("Claude Agent SDK workflow failed")
            raise AgentError("Claude Agent SDK request failed") from exc

    async def _ask_ollama(self, query: str, search_tool: TranscriptSearchTool) -> AgentAnswer:
        if self.local_provider is None:
            raise AgentConfigurationError("Ollama provider is not configured")
        logger.info("Ollama agent retrieval started")
        try:
            results = await search_tool.retrieve({"query": query})
        except Exception as exc:
            logger.exception("Ollama agent retrieval failed")
            raise AgentError("Transcript retrieval failed") from exc
        logger.info("Ollama agent retrieval complete: count=%d", len(results))
        if not results:
            return AgentAnswer(
                "The available transcript evidence is insufficient to answer this question reliably.",
                [],
            )
        context = self._bounded_context(results)
        try:
            answer = await self.local_provider.generate(
                system_prompt=AGENT_SYSTEM_PROMPT,
                user_prompt=(
                    f"Answer this question using only the transcript evidence below:\n{query}\n\n"
                    f"{context}"
                ),
            )
        except LLMProviderError as exc:
            raise AgentError(str(exc)) from exc
        except Exception as exc:
            logger.exception("Ollama agent generation failed")
            raise AgentError("Ollama generation failed") from exc
        return AgentAnswer(answer, [self._source_for(chunk) for chunk in results[:5]])

    @staticmethod
    def _bounded_context(results: list[Any], max_chars: int = 12_000) -> str:
        blocks: list[str] = []
        total = 0
        for index, chunk in enumerate(results[:5], start=1):
            block = (
                f"[S{index}] chunk_id={chunk.id}; episode={chunk.episode_slug}; "
                f"guest={chunk.guest or 'unknown'}; similarity={chunk.relevance_score:.4f}\n"
                f"{chunk.chunk_text}"
            )
            if total + len(block) > max_chars:
                block = block[: max_chars - total].rstrip()
            if not block:
                break
            blocks.append(block)
            total += len(block) + 2
            if total >= max_chars:
                break
        return "\n\n".join(blocks)

    @staticmethod
    def _build_prompt(query: str, top_k: int | None) -> str:
        top_k_instruction = f" Use at most {top_k} results." if top_k is not None else ""
        return (
            f"Answer this user question: {query}\n\n"
            "Search the Lenny transcript corpus first using search_transcripts."
            f"{top_k_instruction}"
        )

    @staticmethod
    def _sdk_api() -> tuple[Any, Any, Any, Any]:
        try:
            from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, create_sdk_mcp_server, tool
        except ImportError as exc:
            raise AgentConfigurationError(
                "claude-agent-sdk is not installed in the project environment"
            ) from exc
        return ClaudeSDKClient, tool, create_sdk_mcp_server, ClaudeAgentOptions

    @staticmethod
    def _make_sdk_tool(tool_decorator: Any, search_tool: TranscriptSearchTool) -> Any:
        @tool_decorator(
            "search_transcripts",
            "Search Lenny podcast transcripts for grounded evidence.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 2000},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                    "episode": {"type": "string"},
                    "guest": {"type": "string"},
                },
                "required": ["query"],
            },
        )
        async def search_transcripts(arguments: dict) -> dict:
            return await search_tool.search(arguments)

        return search_transcripts

    @staticmethod
    def _text_blocks(message: Any) -> list[str]:
        try:
            from claude_agent_sdk import AssistantMessage, TextBlock
        except ImportError:
            return []
        if not isinstance(message, AssistantMessage):
            return []
        return [block.text for block in message.content if isinstance(block, TextBlock)]

    @staticmethod
    def _source_for(chunk: Any) -> SourceCitation:
        return SourceCitation(
            chunk_id=chunk.id,
            episode_slug=chunk.episode_slug,
            guest=chunk.guest,
            title=chunk.title,
            chunk_index=chunk.chunk_index,
            similarity_score=chunk.relevance_score,
            youtube_url=chunk.youtube_url,
        )
