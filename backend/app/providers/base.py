from typing import Protocol


class LLMProviderError(RuntimeError):
    """Raised when a configured local/cloud model cannot generate a response."""


class LLMProvider(Protocol):
    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from bounded, caller-provided context."""
