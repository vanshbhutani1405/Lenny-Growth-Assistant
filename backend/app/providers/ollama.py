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
        timeout_seconds: float = 300.0,
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

    async def stream_generate(self, *, system_prompt: str, user_prompt: str):
        self._first_token_logged = False
        payload = {
            "model": self.model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        logger.info("Ollama streaming generation started: model=%s", self.model)
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()
        sentinel = object()

        def produce() -> None:
            try:
                for token in self._stream_post(payload):
                    loop.call_soon_threadsafe(queue.put_nowait, token)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, sentinel)

        task = asyncio.create_task(asyncio.to_thread(produce))
        try:
            while True:
                item = await queue.get()
                if item is sentinel:
                    break
                if isinstance(item, Exception):
                    raise LLMProviderError("Ollama streaming request failed") from item
                token = str(item)
                if not getattr(self, "_first_token_logged", False):
                    logger.info("Ollama first token received: model=%s streaming=true", self.model)
                    self._first_token_logged = True
                yield token
        finally:
            await task
        logger.info("Ollama streaming generation completed")

    def _post(self, payload: dict) -> dict:
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        logger.info(
            "Ollama request starting: model=%s timeout_seconds=%s streaming=%s",
            self.model,
            self.timeout_seconds,
            bool(payload.get("stream")),
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMProviderError(f"Ollama returned HTTP {exc.code}: {detail[:300]}") from exc
        except URLError as exc:
            raise LLMProviderError(f"Ollama is unavailable at {self.base_url}") from exc

    def _stream_post(self, payload: dict):
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        logger.info(
            "Ollama request starting: model=%s timeout_seconds=%s streaming=%s",
            self.model,
            self.timeout_seconds,
            bool(payload.get("stream")),
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                for raw_line in response:
                    if not raw_line.strip():
                        continue
                    message = json.loads(raw_line.decode("utf-8"))
                    content = message.get("message", {}).get("content", "")
                    if content:
                        yield content
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMProviderError(f"Ollama returned HTTP {exc.code}: {detail[:300]}") from exc
        except URLError as exc:
            raise LLMProviderError(f"Ollama is unavailable at {self.base_url}") from exc
