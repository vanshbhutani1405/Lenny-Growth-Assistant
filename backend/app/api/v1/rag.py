from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.rag.generator import (
    GenerationError,
    GroundedAnswerGenerator,
    UnavailableLLMClient,
)
from app.rag.retriever import Retriever
from app.schemas.rag import RagAskRequest, RagAskResponse, RagSource

router = APIRouter(prefix="/rag", tags=["rag"])


def get_answer_generator(session: AsyncSession = Depends(get_db_session)) -> GroundedAnswerGenerator:
    return GroundedAnswerGenerator(Retriever(session), UnavailableLLMClient())


@router.post("/ask", response_model=RagAskResponse)
async def ask_rag(
    request: RagAskRequest,
    generator: GroundedAnswerGenerator = Depends(get_answer_generator),
) -> RagAskResponse:
    try:
        result = await generator.ask(
            request.query,
            top_k=request.top_k,
            episode=request.episode,
            guest=request.guest,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "rag_unavailable", "message": str(exc)},
        ) from exc
    return RagAskResponse(
        answer=result.answer,
        sources=[RagSource(**asdict(source)) for source in result.sources],
    )
