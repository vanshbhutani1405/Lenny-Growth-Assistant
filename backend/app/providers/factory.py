from app.core.config import Settings
from app.providers.base import LLMProvider
from app.providers.ollama import OllamaProvider


class ProviderConfigurationError(ValueError):
    """Raised when the configured LLM provider is unsupported."""


def select_local_provider(settings: Settings) -> LLMProvider | None:
    provider = getattr(settings, "llm_provider", "claude").strip().lower()
    if provider == "claude":
        return None
    if provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    raise ProviderConfigurationError(f"Unsupported LLM_PROVIDER: {provider}")
