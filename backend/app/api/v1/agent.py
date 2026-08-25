from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import AgentError, LennyAgent
from app.core.config import get_settings
from app.database.session import get_db_session
from app.rag.retriever import Retriever
from app.schemas.agent import AgentAskRequest, AgentAskResponse
from app.schemas.rag import RagSource

router = APIRouter(prefix="/agent", tags=["agent"])


def get_lenny_agent(session: AsyncSession = Depends(get_db_session)) -> LennyAgent:
    return LennyAgent(Retriever(session), get_settings())


@router.post("/ask", response_model=AgentAskResponse)
async def ask_agent(
    request: AgentAskRequest,
    agent: LennyAgent = Depends(get_lenny_agent),
) -> AgentAskResponse:
    try:
        result = await agent.ask(request.query, top_k=request.top_k)
    except AgentError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "agent_unavailable", "message": str(exc)},
        ) from exc
    return AgentAskResponse(
        answer=result.answer,
        sources=[RagSource(**asdict(source)) for source in result.sources],
    )
