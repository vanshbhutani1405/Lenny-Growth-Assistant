import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.agent.agent import AgentConversation, LennyAgent

logger = logging.getLogger(__name__)


class SessionNotFoundError(LookupError):
    """Raised when a requested in-memory session does not exist or expired."""


@dataclass(slots=True)
class SessionState:
    session_id: str
    conversation: AgentConversation
    last_accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SessionManager:
    """Owns bounded in-memory conversation state; no transcript data is persisted here."""

    def __init__(self, *, ttl_hours: int = 24) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._ttl = timedelta(hours=ttl_hours)

    async def create(self, agent: LennyAgent) -> SessionState:
        session_id = str(uuid4())
        state = SessionState(session_id, agent.new_conversation(session_id))
        self._sessions[session_id] = state
        logger.info("Agent session created: session_id=%s", session_id)
        return state

    async def get(self, session_id: str, agent: LennyAgent) -> SessionState:
        state = self._sessions.get(session_id)
        if state is None:
            raise SessionNotFoundError(session_id)
        if datetime.now(UTC) - state.last_accessed_at > self._ttl:
            await self.clear(session_id)
            raise SessionNotFoundError(session_id)
        state.conversation.rebind_agent(agent)
        state.last_accessed_at = datetime.now(UTC)
        logger.info("Agent session continued: session_id=%s", session_id)
        return state

    async def get_or_create(self, session_id: str | None, agent: LennyAgent) -> SessionState:
        if session_id is None:
            return await self.create(agent)
        return await self.get(session_id, agent)

    async def clear(self, session_id: str) -> None:
        state = self._sessions.pop(session_id, None)
        if state is not None:
            await state.conversation.close()
            logger.info("Agent session cleared: session_id=%s", session_id)

    async def cleanup_expired(self) -> int:
        cutoff = datetime.now(UTC) - self._ttl
        expired = [
            session_id
            for session_id, state in self._sessions.items()
            if state.last_accessed_at < cutoff
        ]
        for session_id in expired:
            await self.clear(session_id)
        return len(expired)


session_manager = SessionManager()
