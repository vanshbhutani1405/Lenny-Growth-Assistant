import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import AgentConversation, LennyAgent
from app.models.conversation_message import ConversationMessage
from app.models.conversation_session import ConversationSession

logger = logging.getLogger(__name__)


class SessionNotFoundError(LookupError):
    """Raised when a requested durable conversation does not exist."""


class SessionPersistenceError(RuntimeError):
    """Raised when a conversation cannot be read or written durably."""


@dataclass(slots=True)
class SessionState:
    session_id: str
    conversation: AgentConversation
    last_accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    persistence_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class SessionManager:
    """PostgreSQL-backed sessions with an in-memory conversation optimization."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    async def create(self, agent: LennyAgent, db_session: AsyncSession, *, user_metadata: dict | None = None) -> SessionState:
        session_id = str(uuid4())
        db_session.add(ConversationSession(id=session_id, user_metadata=user_metadata))
        try:
            await db_session.commit()
        except SQLAlchemyError as exc:
            await db_session.rollback()
            raise SessionPersistenceError("Could not create the conversation session.") from exc
        state = SessionState(session_id, agent.new_conversation(session_id))
        self._sessions[session_id] = state
        logger.info("Persistent session created: session_id=%s", session_id)
        return state

    async def get(self, session_id: str, agent: LennyAgent, db_session: AsyncSession) -> SessionState:
        _, messages = await self._load(session_id, db_session)
        state = self._sessions.get(session_id)
        if state is None or state.conversation._closed:
            state = SessionState(session_id, agent.new_conversation(session_id))
            self._sessions[session_id] = state
        else:
            state.conversation.rebind_agent(agent)
        state.conversation.replace_history(self._history_from_messages(messages))
        state.last_accessed_at = datetime.now(UTC)
        logger.info("Persistent session continued: session_id=%s messages=%d", session_id, len(messages))
        return state

    async def get_or_create(self, session_id: str | None, agent: LennyAgent, db_session: AsyncSession) -> SessionState:
        return await self.create(agent, db_session) if session_id is None else await self.get(session_id, agent, db_session)

    async def record_turn(self, state: SessionState, db_session: AsyncSession, query: str, answer: str, *, provider: str | None = None, workflow: str | None = None) -> None:
        async with state.persistence_lock:
            try:
                sequence = await self._next_sequence(state.session_id, db_session)
                db_session.add_all([
                    ConversationMessage(session_id=state.session_id, role="user", content=query, sequence=sequence),
                    ConversationMessage(session_id=state.session_id, role="assistant", content=answer, sequence=sequence + 1),
                ])
                await self._touch_session(state.session_id, db_session, provider, workflow)
                await db_session.commit()
            except SQLAlchemyError as exc:
                await db_session.rollback()
                logger.exception("Conversation turn persistence failed: session_id=%s", state.session_id)
                raise SessionPersistenceError("Could not persist the conversation turn.") from exc

    async def record_user_message(self, state: SessionState, db_session: AsyncSession, query: str, *, provider: str | None = None, workflow: str | None = None) -> None:
        await self._record_single(state, db_session, "user", query, provider=provider, workflow=workflow)

    async def record_assistant_message(self, state: SessionState, db_session: AsyncSession, answer: str, *, provider: str | None = None, workflow: str | None = None) -> None:
        await self._record_single(state, db_session, "assistant", answer, provider=provider, workflow=workflow)

    async def _record_single(self, state: SessionState, db_session: AsyncSession, role: str, content: str, *, provider: str | None, workflow: str | None) -> None:
        async with state.persistence_lock:
            try:
                sequence = await self._next_sequence(state.session_id, db_session)
                db_session.add(ConversationMessage(session_id=state.session_id, role=role, content=content, sequence=sequence))
                await self._touch_session(state.session_id, db_session, provider, workflow)
                await db_session.commit()
            except SQLAlchemyError as exc:
                await db_session.rollback()
                logger.exception("Conversation message persistence failed: session_id=%s role=%s", state.session_id, role)
                raise SessionPersistenceError("Could not persist the conversation message.") from exc

    async def clear(self, session_id: str, db_session: AsyncSession) -> None:
        row = await db_session.scalar(select(ConversationSession).where(ConversationSession.id == session_id))
        if row is None:
            raise SessionNotFoundError(session_id)
        try:
            await db_session.execute(delete(ConversationSession).where(ConversationSession.id == session_id))
            await db_session.commit()
        except SQLAlchemyError as exc:
            await db_session.rollback()
            raise SessionPersistenceError("Could not delete the conversation session.") from exc
        state = self._sessions.pop(session_id, None)
        if state is not None:
            await state.conversation.close()
        logger.info("Persistent session deleted: session_id=%s", session_id)

    async def list_sessions(self, db_session: AsyncSession) -> list[ConversationSession]:
        try:
            result = await db_session.scalars(select(ConversationSession).order_by(ConversationSession.updated_at.desc()))
            return list(result)
        except SQLAlchemyError as exc:
            raise SessionPersistenceError("Could not load conversation sessions.") from exc

    async def get_detail(self, session_id: str, db_session: AsyncSession) -> tuple[ConversationSession, list[ConversationMessage]]:
        return await self._load(session_id, db_session)

    async def _load(self, session_id: str, db_session: AsyncSession) -> tuple[ConversationSession, list[ConversationMessage]]:
        try:
            row = await db_session.scalar(select(ConversationSession).where(ConversationSession.id == session_id))
            if row is None:
                raise SessionNotFoundError(session_id)
            result = await db_session.scalars(select(ConversationMessage).where(ConversationMessage.session_id == session_id).order_by(ConversationMessage.sequence, ConversationMessage.created_at))
            return row, list(result)
        except SessionNotFoundError:
            raise
        except SQLAlchemyError as exc:
            raise SessionPersistenceError("Could not load the conversation session.") from exc

    @staticmethod
    async def _next_sequence(session_id: str, db_session: AsyncSession) -> int:
        value = await db_session.scalar(select(func.coalesce(func.max(ConversationMessage.sequence), -1)).where(ConversationMessage.session_id == session_id))
        return int(value) + 1

    @staticmethod
    async def _touch_session(session_id: str, db_session: AsyncSession, provider: str | None, workflow: str | None) -> None:
        values: dict = {"updated_at": func.now()}
        if provider is not None:
            values["provider"] = provider
        if workflow is not None:
            values["workflow"] = workflow
        await db_session.execute(update(ConversationSession).where(ConversationSession.id == session_id).values(**values))

    @staticmethod
    def _history_from_messages(messages: list[ConversationMessage]) -> list[tuple[str, str]]:
        history: list[tuple[str, str]] = []
        pending_user: str | None = None
        for message in messages:
            if message.role == "user":
                pending_user = message.content
            elif message.role == "assistant" and pending_user is not None:
                history.append((pending_user, message.content))
                pending_user = None
        if pending_user is not None:
            history.append((pending_user, ""))
        return history


session_manager = SessionManager()
