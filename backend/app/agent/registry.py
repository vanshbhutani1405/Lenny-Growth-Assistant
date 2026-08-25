from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.agent.artifact import ArtifactTool
from app.agent.ship30 import Ship30Tool
from app.agent.tools import TranscriptSearchTool


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    handler: Callable[[dict], Awaitable[dict]]


class AgentToolRegistry:
    """Single registry for tools exposed through Claude's in-process MCP server."""

    def __init__(self, transcript_search: TranscriptSearchTool) -> None:
        self.specs = [
            self._spec(Ship30Tool()),
            self._spec(ArtifactTool()),
            self._spec(transcript_search, name="search_transcripts", description="Search Lenny podcast transcripts for grounded evidence.", schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 2000},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                    "episode": {"type": "string"},
                    "guest": {"type": "string"},
                },
                "required": ["query"],
            }, handler=transcript_search.search),
        ]

    @staticmethod
    def _spec(tool: Any, *, name: str | None = None, description: str | None = None,
              schema: dict | None = None, handler: Callable | None = None) -> ToolSpec:
        return ToolSpec(
            name=name or getattr(tool, "name"),
            description=description or getattr(tool, "description"),
            input_schema=schema or getattr(tool, "input_schema"),
            handler=handler or getattr(tool, "validate", None) or getattr(tool, "create"),
        )

    def sdk_tools(self, tool_decorator: Any) -> list[Any]:
        sdk_tools = []
        for spec in self.specs:
            @tool_decorator(spec.name, spec.description, spec.input_schema)
            async def sdk_tool(arguments: dict, handler=spec.handler) -> dict:
                return await handler(arguments)

            sdk_tool.__name__ = spec.name
            sdk_tools.append(sdk_tool)
        return sdk_tools

    @property
    def allowed_tool_names(self) -> list[str]:
        return [f"mcp__lenny__{spec.name}" for spec in self.specs]
