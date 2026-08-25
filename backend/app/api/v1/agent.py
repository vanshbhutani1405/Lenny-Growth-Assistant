from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import AgentError, LennyAgent
from app.agent.sessions import SessionNotFoundError, session_manager
from app.core.config import get_settings
from app.database.session import get_db_session
from app.rag.retriever import Retriever
from app.schemas.agent import AgentAskRequest, AgentAskResponse
from app.schemas.rag import RagSource
from app.observability.tracing import traced

router = APIRouter(prefix="/agent", tags=["agent"])


def get_lenny_agent(session: AsyncSession = Depends(get_db_session)) -> LennyAgent:
    settings = get_settings()
    return LennyAgent(Retriever(session), settings)


@router.post("/ask", response_model=AgentAskResponse)
@traced("api.agent.ask", run_type="chain")
async def ask_agent(
    request: AgentAskRequest,
    agent: LennyAgent = Depends(get_lenny_agent),
) -> AgentAskResponse:
    try:
        state = await session_manager.get_or_create(request.session_id, agent)
        result = await state.conversation.ask(request.query, top_k=request.top_k)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "session_not_found", "message": "The session does not exist or has expired."},
        ) from exc
    except AgentError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "agent_unavailable", "message": str(exc)},
        ) from exc
    return AgentAskResponse(
        session_id=state.session_id,
        answer=result.answer,
        sources=[RagSource(**asdict(source)) for source in result.sources],
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def clear_agent_session(session_id: str) -> None:
    await session_manager.clear(session_id)
