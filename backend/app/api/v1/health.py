from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db_session
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()
    model = settings.ollama_model if provider == "ollama" else settings.claude_model
    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        provider=provider,
        model=model,
    )


@router.get("/health/db", response_model=DatabaseHealthResponse)
async def database_health(session: AsyncSession = Depends(get_db_session)) -> DatabaseHealthResponse:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "database_unavailable", "message": "Database is unavailable"},
        ) from exc
    return DatabaseHealthResponse(status="ok", database="reachable")
