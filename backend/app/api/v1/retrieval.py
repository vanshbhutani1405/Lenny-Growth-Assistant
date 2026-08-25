from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.rag.retrieval import RetrievalService
from app.schemas.retrieval import RetrievalResult, RetrievalSearchRequest, RetrievalSearchResponse

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_retrieval(
    request: RetrievalSearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RetrievalSearchResponse:
    result = await RetrievalService(session).search(
        request.query,
        request.top_k,
        {"episode_slug": request.episode_slug, "guest": request.guest},
    )
    return RetrievalSearchResponse(
        query=request.query,
        results=[
            RetrievalResult(**{**asdict(item), "retrieval_sources": list(item.retrieval_sources)})
            for item in result.results
        ],
        attempted_correction=result.attempted_correction,
        corrective_query=result.corrective_query,
    )
