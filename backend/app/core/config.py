from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", validation_alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, validation_alias="EMBEDDING_DIMENSION")
    chunk_size_words: int = Field(default=400, validation_alias="CHUNK_SIZE_WORDS")
    chunk_overlap_words: int = Field(default=60, validation_alias="CHUNK_OVERLAP_WORDS")
    retrieval_top_k: int = Field(default=8, validation_alias="RETRIEVAL_TOP_K")
    retrieval_min_score: float = Field(default=0.18, validation_alias="RETRIEVAL_MIN_SCORE")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-sonnet-4-5", validation_alias="CLAUDE_MODEL")
    llm_provider: str = Field(default="ollama", validation_alias="LLM_PROVIDER")
    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2:1b", validation_alias="OLLAMA_MODEL")
    langchain_tracing_v2: bool = Field(default=False, validation_alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str | None = Field(default=None, validation_alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="lenny-growth-assistant", validation_alias="LANGCHAIN_PROJECT")
    frontend_origin: str = Field(default="http://localhost:5173", validation_alias="FRONTEND_ORIGIN")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return "postgresql+asyncpg://" + self.database_url.removeprefix("postgres://")
        if self.database_url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + self.database_url.removeprefix("postgresql://")
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
