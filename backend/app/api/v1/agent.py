import json
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import AgentError, LennyAgent
from app.agent.sessions import SessionNotFoundError, SessionPersistenceError, session_manager
from app.core.config import get_settings
from app.database.session import get_db_session
from app.observability.tracing import traced
from app.rag.retriever import Retriever
from app.schemas.agent import (
    AgentAskRequest,
    AgentAskResponse,
    AgentSessionDetail,
    AgentSessionMessage,
    AgentSessionSummary,
)
from app.schemas.rag import RagSource

router = APIRouter(prefix="/agent", tags=["agent"])


def get_lenny_agent(session: AsyncSession = Depends(get_db_session)) -> LennyAgent:
    return LennyAgent(Retriever(session), get_settings())


def _session_metadata(agent: LennyAgent, query: str) -> tuple[str, str]:
    provider = getattr(agent.settings, "llm_provider", "claude").strip().lower()
    workflow = agent.workflow_router.route(query).intent.value
    return provider, workflow


def _persistence_error(exc: SessionPersistenceError) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={"code": "session_persistence_unavailable", "message": str(exc)},
    )


@router.post("/ask", response_model=AgentAskResponse)
@traced("api.agent.ask", run_type="chain")
async def ask_agent(
    request: AgentAskRequest,
    agent: LennyAgent = Depends(get_lenny_agent),
    db_session: AsyncSession = Depends(get_db_session),
) -> AgentAskResponse:
    try:
        state = await session_manager.get_or_create(request.session_id, agent, db_session)
        result = await state.conversation.ask(request.query, top_k=request.top_k)
        provider, workflow = _session_metadata(agent, request.query)
        await session_manager.record_turn(
            state, db_session, request.query.strip(), result.answer, provider=provider, workflow=workflow
        )
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "The session does not exist."},
        ) from exc
    except SessionPersistenceError as exc:
        raise _persistence_error(exc) from exc
    except AgentError as exc:
        raise HTTPException(status_code=503, detail={"code": "agent_unavailable", "message": str(exc)}) from exc
    return AgentAskResponse(
        session_id=state.session_id,
        answer=result.answer,
        sources=[RagSource(**asdict(source)) for source in result.sources],
    )


@router.get("/sessions", response_model=list[AgentSessionSummary])
async def list_agent_sessions(
    db_session: AsyncSession = Depends(get_db_session),
) -> list[AgentSessionSummary]:
    try:
        rows = await session_manager.list_sessions(db_session)
    except SessionPersistenceError as exc:
        raise _persistence_error(exc) from exc
    return [
        AgentSessionSummary(
            session_id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            provider=row.provider,
            workflow=row.workflow,
        )
        for row in rows
    ]


@router.get("/sessions/{session_id}", response_model=AgentSessionDetail)
async def get_agent_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_db_session),
) -> AgentSessionDetail:
    try:
        row, messages = await session_manager.get_detail(session_id, db_session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "The session does not exist."}) from exc
    except SessionPersistenceError as exc:
        raise _persistence_error(exc) from exc
    return AgentSessionDetail(
        session_id=row.id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        provider=row.provider,
        workflow=row.workflow,
        messages=[
            AgentSessionMessage(
                id=message.id,
                role=message.role,
                content=message.content,
                sequence=message.sequence,
                created_at=message.created_at,
            )
            for message in messages
        ],
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def clear_agent_session(
    session_id: str,
    db_session: AsyncSession = Depends(get_db_session),
) -> None:
    try:
        await session_manager.clear(session_id, db_session)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "The session does not exist."}) from exc
    except SessionPersistenceError as exc:
        raise _persistence_error(exc) from exc


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.post("/ask/stream")
async def stream_agent(
    request: AgentAskRequest,
    agent: LennyAgent = Depends(get_lenny_agent),
    db_session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    try:
        state = await session_manager.get_or_create(request.session_id, agent, db_session)
        provider, workflow = _session_metadata(agent, request.query)
        await session_manager.record_user_message(
            state, db_session, request.query.strip(), provider=provider, workflow=workflow
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "The session does not exist."}) from exc
    except SessionPersistenceError as exc:
        raise _persistence_error(exc) from exc

    async def events():
        yield _sse("session", {"session_id": state.session_id})
        assistant_parts: list[str] = []
        completed_event: dict | None = None
        try:
            async for event in state.conversation.stream(request.query, top_k=request.top_k):
                if event["event"] == "token":
                    assistant_parts.append(event["data"].get("token", ""))
                if event["event"] == "done":
                    completed_event = event
                    continue
                yield _sse(event["event"], event["data"])
            if completed_event is None:
                raise AgentError("Stream completed without a final event")
            await session_manager.record_assistant_message(
                state,
                db_session,
                "".join(assistant_parts).strip(),
                provider=provider,
                workflow=workflow,
            )
            yield _sse(completed_event["event"], completed_event["data"])
        except SessionPersistenceError as exc:
            yield _sse("error", {"code": "session_persistence_unavailable", "message": str(exc)})
        except AgentError as exc:
            yield _sse("error", {"code": "agent_unavailable", "message": str(exc)})
        except Exception:
            yield _sse("error", {"code": "stream_failed", "message": "The streamed response failed."})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
