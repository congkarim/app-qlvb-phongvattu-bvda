import hashlib
import logging
import math
from functools import cached_property
from pathlib import Path
from typing import Any

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class EmbeddingModelUnavailableError(RuntimeError):
    pass


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.dimensions = self.settings.embedding_dimensions
        self.backend = self.settings.embedding_backend.lower()

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.backend == "fake":
            return [self._fake_embed(text) for text in texts]
        if self.backend == "sentence_transformers":
            return self._embed_with_sentence_transformers(texts)
        raise ValueError(f"Unsupported embedding backend: {self.settings.embedding_backend}")

    def _fake_embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self.dimensions):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) - 0.5)

        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    def _embed_with_sentence_transformers(self, texts: list[str]) -> list[list[float]]:
        try:
            vectors = self.model.encode(
                texts,
                batch_size=self.settings.embedding_batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            if self.settings.allow_fake_embeddings:
                logger.warning("Falling back to fake embeddings because local model failed: %s", exc)
                return [self._fake_embed(text) for text in texts]
            raise EmbeddingModelUnavailableError(f"Local embedding model failed: {exc}") from exc

        output = [vector.astype(float).tolist() for vector in vectors]
        for vector in output:
            if len(vector) != self.dimensions:
                raise ValueError(
                    "Embedding dimension mismatch: "
                    f"expected {self.dimensions}, got {len(vector)}. "
                    "Check EMBEDDING_DIMENSIONS and QDRANT_COLLECTION."
                )
        return output

    @cached_property
    def model(self) -> Any:
        model_path = self._resolve_model_path()
        try:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(
                str(model_path),
                device=self.settings.embedding_device,
                local_files_only=self.settings.embedding_local_files_only,
            )
        except Exception as exc:
            if self.settings.allow_fake_embeddings:
                logger.warning("Local embedding model unavailable, fake fallback is enabled: %s", exc)
                return _UnavailableEmbeddingModel(exc)
            raise EmbeddingModelUnavailableError(
                f"Local embedding model unavailable at {model_path}. "
                "Prepare the model locally or enable ALLOW_FAKE_EMBEDDINGS=true for development."
            ) from exc

    def _resolve_model_path(self) -> Path | str:
        if self.settings.embedding_model_path:
            return self.settings.embedding_model_path
        return self.settings.embedding_model_name


class _UnavailableEmbeddingModel:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def encode(self, *_args: Any, **_kwargs: Any) -> list[list[float]]:
        raise self.error
