import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.registry import AgentToolRegistry
from app.agent.ship30 import Ship30Tool
from app.agent.tools import TranscriptSearchTool
from app.agent.workflows import WorkflowPlan, WorkflowRouter
from app.core.config import Settings
from app.providers.base import LLMProvider, LLMProviderError
from app.providers.factory import select_local_provider
from app.rag.generator import SourceCitation
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)


class AgentError(RuntimeError):
    """Raised when an agent request cannot complete."""


class AgentConfigurationError(AgentError):
    """Raised when Claude or the configured provider is unavailable."""


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
        workflow_router: WorkflowRouter | None = None,
    ) -> None:
        self.retriever = retriever
        self.settings = settings
        self.local_provider = local_provider if local_provider is not None else select_local_provider(settings)
        self.workflow_router = workflow_router or WorkflowRouter()

    def new_conversation(self, session_id: str) -> "AgentConversation":
        return AgentConversation(self, session_id)

    async def ask(self, query: str, *, top_k: int | None = None) -> AgentAnswer:
        """Preserve the stateless interface for callers that do not need a session."""
        conversation = self.new_conversation("ephemeral")
        try:
            return await conversation.ask(query, top_k=top_k)
        finally:
            await conversation.close()

    def _build_claude_client(self, search_tool: TranscriptSearchTool) -> Any:
        client_class, tool_decorator, server_factory, options_class = self._sdk_api()
        registry = AgentToolRegistry(search_tool)
        sdk_tools = registry.sdk_tools(tool_decorator)
        server = server_factory(name="lenny-tools", tools=sdk_tools)
        options = options_class(
            model=self.settings.claude_model,
            system_prompt=AGENT_SYSTEM_PROMPT,
            max_turns=3,
            mcp_servers={"lenny": server},
            allowed_tools=registry.allowed_tool_names,
        )
        return client_class(options=options)

    async def _run_claude_query(
        self,
        client: Any,
        query: str,
        top_k: int | None,
        search_tool: TranscriptSearchTool,
        workflow: WorkflowPlan,
    ) -> AgentAnswer:
        logger.info("Claude generation started: model=%s", self.settings.claude_model)
        answer_parts: list[str] = []
        await client.query(workflow.prompt(query, top_k))
        async for message in client.receive_response():
            answer_parts.extend(self._text_blocks(message))
        answer = "\n".join(part for part in answer_parts if part).strip()
        if not answer:
            raise AgentError("Claude returned an empty answer")
        logger.info("Claude generation completed: sources=%d", len(search_tool.last_results))
        return AgentAnswer(answer, [self._source_for(chunk) for chunk in search_tool.last_results])

    async def _ask_ollama(
        self,
        query: str,
        search_tool: TranscriptSearchTool,
        history: list[tuple[str, str]],
        workflow: WorkflowPlan,
    ) -> AgentAnswer:
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
        prior_context = self._bounded_history(history)
        try:
            answer = await self.local_provider.generate(
                system_prompt=AGENT_SYSTEM_PROMPT,
                user_prompt=(
                    f"Prior conversation context (not transcript evidence):\n{prior_context}\n\n"
                    f"Current question:\n{query}\n\n"
                    f"Current transcript evidence:\n{context}\n\n"
                    f"Workflow instructions:\n{workflow.instruction}"
                ),
            )
        except LLMProviderError as exc:
            raise AgentError(str(exc)) from exc
        except Exception as exc:
            logger.exception("Ollama agent generation failed")
            raise AgentError("Ollama generation failed") from exc
        logger.info("Ollama generation completed: sources=%d", len(results))
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
    def _bounded_history(history: list[tuple[str, str]], max_chars: int = 4_000) -> str:
        lines: list[str] = []
        total = 0
        for query, answer in history[-6:]:
            line = f"User: {query}\nAssistant: {answer}"
            if total + len(line) > max_chars:
                line = line[: max_chars - total].rstrip()
            if not line:
                break
            lines.append(line)
            total += len(line) + 2
            if total >= max_chars:
                break
        return "\n\n".join(lines) or "(none)"

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


class AgentConversation:
    """Provider-neutral multi-turn state for one in-memory session."""

    def __init__(self, agent: LennyAgent, session_id: str) -> None:
        self.agent = agent
        self.session_id = session_id
        self.search_tool = TranscriptSearchTool(agent.retriever)
        self.history: list[tuple[str, str]] = []
        self._claude_client: Any | None = None
        self._closed = False
        self._lock = asyncio.Lock()

    def rebind_agent(self, agent: LennyAgent) -> None:
        self.agent = agent
        self.search_tool.retriever = agent.retriever

    async def ask(self, query: str, *, top_k: int | None = None) -> AgentAnswer:
        normalized_query = query.strip()
        if not normalized_query:
            raise AgentError("query must not be empty")
        if self._closed:
            raise AgentError("session is closed")
        async with self._lock:
            logger.info("Continuing agent session: session_id=%s", self.session_id)
            provider = getattr(self.agent.settings, "llm_provider", "claude").strip().lower()
            workflow = self.agent.workflow_router.route(normalized_query)
            try:
                if provider == "claude":
                    answer = await self._ask_claude(normalized_query, top_k, workflow)
                elif provider == "ollama":
                    self.search_tool.default_top_k = top_k
                    answer = await self.agent._ask_ollama(
                        normalized_query,
                        self.search_tool,
                        self.history,
                        workflow,
                    )
                else:
                    raise AgentConfigurationError(f"Unsupported LLM_PROVIDER: {provider}")
            except AgentError:
                raise
            except Exception as exc:
                logger.exception("Agent session request failed: session_id=%s", self.session_id)
                raise AgentError("Agent session request failed") from exc
            answer = await self._validate_workflow(
                normalized_query,
                top_k,
                workflow,
                answer,
                provider,
            )
            self.history.append((normalized_query, answer.answer))
            return answer

    async def _ask_claude(
        self,
        query: str,
        top_k: int | None,
        workflow: WorkflowPlan,
    ) -> AgentAnswer:
        if self._claude_client is None:
            self._claude_client = self.agent._build_claude_client(self.search_tool)
            await self._claude_client.__aenter__()
        return await self.agent._run_claude_query(
            self._claude_client,
            query,
            top_k,
            self.search_tool,
            workflow,
        )

    async def _validate_workflow(
        self,
        query: str,
        top_k: int | None,
        workflow: WorkflowPlan,
        answer: AgentAnswer,
        provider: str,
    ) -> AgentAnswer:
        if not workflow.requires_ship30_validation or not answer.sources:
            return answer
        validator = Ship30Tool()
        validation = await validator.validate({"draft": answer.answer, "redraft_attempt": 0})
        payload = self._tool_payload(validation)
        if payload.get("valid") or not payload.get("redraft_allowed"):
            return answer

        logger.info("Ship 30 corrective redraft started: session_id=%s", self.session_id)
        retry_query = (
            f"{query}\n\nThe first draft failed validation with these issues: "
            f"{', '.join(payload.get('issues', []))}. Produce one corrected draft only."
        )
        if provider == "claude":
            redraft = await self._ask_claude(retry_query, top_k, workflow)
        else:
            redraft = await self.agent._ask_ollama(
                retry_query,
                self.search_tool,
                self.history,
                workflow,
            )
        await validator.validate({"draft": redraft.answer, "redraft_attempt": 1})
        logger.info("Ship 30 corrective redraft completed: session_id=%s", self.session_id)
        return redraft

    @staticmethod
    def _tool_payload(result: dict) -> dict:
        try:
            return json.loads(result["content"][0]["text"])
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return {"valid": False, "redraft_allowed": False}

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._claude_client is not None:
            await self._claude_client.__aexit__(None, None, None)
            self._claude_client = None
        logger.info("Agent session cleaned up: session_id=%s", self.session_id)
