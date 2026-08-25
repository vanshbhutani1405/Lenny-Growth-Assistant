from functools import lru_cache
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Lazy local SentenceTransformer wrapper; no network embedding API is used."""

    def __init__(self, model_name: str | None = None, dimension: int | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dimension = dimension or settings.embedding_dimension
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - dependency installation concern
                raise RuntimeError(
                    "sentence-transformers is required for local embeddings"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
            actual_dimension = self._model.get_embedding_dimension()
            if actual_dimension != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: configured {self.dimension}, model returned {actual_dimension}"
                )
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        batch_size = 32
        model = self._load_model()
        device = getattr(model, "device", "unknown")
        logger.info(
            "Starting SentenceTransformer.encode: model=%s device=%s chunks=%d batch_size=%d",
            self.model_name,
            device,
            len(texts),
            batch_size,
        )
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        logger.info(
            "Completed SentenceTransformer.encode: model=%s device=%s chunks=%d",
            self.model_name,
            device,
            len(texts),
        )
        return [list(map(float, vector)) for vector in vectors]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
