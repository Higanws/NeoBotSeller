"""Generación de vectores — local (fastembed) u OpenAI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from embedding_service.config import Settings

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._local_model = None
        self._vector_size: int | None = None

    @property
    def vector_size(self) -> int:
        if self._vector_size is None:
            self._vector_size = len(self.embed_text("dimension probe"))
        return self._vector_size

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.settings.embedding_provider == "openai":
            return self._embed_openai(texts)
        return self._embed_local(texts)

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        from fastembed import TextEmbedding

        if self._local_model is None:
            logger.info("Cargando modelo local %s", self.settings.embedding_model)
            self._local_model = TextEmbedding(model_name=self.settings.embedding_model)

        vectors = [list(v) for v in self._local_model.embed(texts)]
        return vectors

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        api_key = self.settings.openai_api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY requerida para EMBEDDING_PROVIDER=openai")

        payload = {"model": self.settings.openai_embedding_model, "input": texts}
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()["data"]
        return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]
