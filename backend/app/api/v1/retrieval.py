from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.rag.retriever import RetrievalError, Retriever
from app.schemas.retrieval import RetrievalResult, RetrievalSearchRequest, RetrievalSearchResponse

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_retrieval(
    request: RetrievalSearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RetrievalSearchResponse:
    try:
        results = await Retriever(session).search(
            query=request.query,
            top_k=request.top_k,
            filters={"episode_slug": request.episode_slug, "guest": request.guest},
        )
    except RetrievalError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "retrieval_unavailable", "message": str(exc)},
        ) from exc
    return RetrievalSearchResponse(
        query=request.query,
        results=[
            RetrievalResult(**{**asdict(item), "retrieval_sources": list(item.retrieval_sources)})
            for item in results
        ],
        attempted_correction=False,
        corrective_query=None,
    )
