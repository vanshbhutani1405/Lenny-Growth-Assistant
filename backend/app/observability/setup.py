import os

from app.core.config import Settings


def configure_langsmith(settings: Settings) -> None:
    """Expose validated settings to LangSmith without making tracing mandatory."""
    if not settings.langchain_tracing_v2 or not settings.langchain_api_key:
        return
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)
