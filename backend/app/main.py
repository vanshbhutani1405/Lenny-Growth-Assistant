from fastapi import FastAPI

from app.api.router import api_router
from app.api.v1.health import router as health_router
from app.api.v1.agent import router as agent_router
from app.api.v1.rag import router as rag_router
from app.api.v1.retrieval import router as retrieval_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Lenny Growth Assistant API",
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )
    application.include_router(health_router)
    application.include_router(health_router, prefix="/api/v1")
    application.include_router(api_router)
    application.include_router(retrieval_router, prefix="/api/v1")
    application.include_router(rag_router, prefix="/api/v1")
    application.include_router(agent_router, prefix="/api/v1")
    return application


app = create_app()
