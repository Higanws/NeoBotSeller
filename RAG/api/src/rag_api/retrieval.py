"""Búsqueda semántica vía embedding-service + Qdrant."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from rag_api.config import Settings
from rag_api.models import RagChunk

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def search(self, query: str) -> list[RagChunk]:
        if not self.settings.rag_enabled:
            return []

        try:
            return self._search_via_embedding_service(query)
        except Exception as exc:
            logger.warning("RAG retrieval no disponible: %s", exc)
            return []

    def _search_via_embedding_service(self, query: str) -> list[RagChunk]:
        base = self.settings.embedding_service_url.rstrip("/")
        top_k = self.settings.rag_top_k

        with httpx.Client(timeout=30.0) as client:
            health = client.get(f"{base}/health", timeout=5.0)
            if health.status_code != 200:
                logger.debug("embedding-service no disponible")
                return []

            response = client.post(
                f"{base}/v1/search",
                json={"query": query, "top_k": top_k},
            )
            response.raise_for_status()
            data = response.json()

        chunks: list[RagChunk] = []
        for item in data.get("chunks", []):
            chunks.append(
                RagChunk(
                    text=item.get("text", ""),
                    score=float(item.get("score", 0.0)),
                    metadata=item.get("metadata", {}),
                )
            )
        return chunks

    def format_context(self, chunks: list[RagChunk]) -> list[dict[str, Any]]:
        return [
            {
                "text": c.text,
                "score": c.score,
                "metadata": c.metadata,
            }
            for c in chunks
        ]
