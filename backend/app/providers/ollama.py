import asyncio
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.providers.base import LLMProviderError
from app.observability.tracing import traced

logger = logging.getLogger(__name__)


class OllamaProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    @traced("provider.ollama.generate", run_type="llm")
    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        logger.info("Ollama generation started: model=%s", self.model)
        try:
            response = await asyncio.to_thread(self._post, payload)
            content = response.get("message", {}).get("content", "").strip()
        except Exception as exc:
            logger.exception("Ollama generation failed")
            raise LLMProviderError("Ollama request failed") from exc
        if not content:
            raise LLMProviderError("Ollama returned an empty response")
        logger.info("Ollama generation completed")
        return content

    def _post(self, payload: dict) -> dict:
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMProviderError(f"Ollama returned HTTP {exc.code}: {detail[:300]}") from exc
        except URLError as exc:
            raise LLMProviderError(f"Ollama is unavailable at {self.base_url}") from exc
