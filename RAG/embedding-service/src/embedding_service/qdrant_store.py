"""Cliente Qdrant — colección y upsert de chunks."""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)


def _point_id(source: str, chunk_index: int) -> str:
    digest = hashlib.sha256(f"{source}:{chunk_index}".encode()).hexdigest()
    return str(uuid.UUID(digest[:32]))


class QdrantStore:
    def __init__(
        self,
        url: str,
        collection: str,
        vector_size: int,
    ) -> None:
        self._client = QdrantClient(url=url)
        self._collection = collection
        self._vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = {c.name for c in self._client.get_collections().collections}
        if self._collection in collections:
            info = self._client.get_collection(self._collection)
            existing_size = info.config.params.vectors.size  # type: ignore[union-attr]
            if existing_size != self._vector_size:
                logger.warning(
                    "Colección %s tiene dim %s, esperada %s",
                    self._collection,
                    existing_size,
                    self._vector_size,
                )
            return

        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=qmodels.VectorParams(
                size=self._vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info(
            "Colección Qdrant creada: %s (dim=%s)",
            self._collection,
            self._vector_size,
        )

    def upsert_chunks(
        self,
        *,
        source: str,
        chunks: list[str],
        vectors: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        if len(chunks) != len(vectors):
            raise ValueError("chunks y vectors deben tener la misma longitud")
        if metadatas and len(metadatas) != len(chunks):
            raise ValueError("metadatas debe tener la misma longitud que chunks")

        points: list[qmodels.PointStruct] = []
        for index, (text, vector) in enumerate(zip(chunks, vectors, strict=True)):
            extra = metadatas[index] if metadatas else {}
            payload: dict[str, Any] = {
                "text": text,
                "source": source,
                "chunk_index": index,
                **extra,
            }
            points.append(
                qmodels.PointStruct(
                    id=_point_id(source, index),
                    vector=vector,
                    payload=payload,
                )
            )

        if not points:
            return 0

        self._client.upsert(collection_name=self._collection, points=points)
        return len(points)

    def search(
        self,
        vector: list[float],
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        results = self._client.search(
            collection_name=self._collection,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
        )
        hits: list[dict[str, Any]] = []
        for hit in results:
            payload = hit.payload or {}
            hits.append(
                {
                    "text": payload.get("text", ""),
                    "score": float(hit.score or 0.0),
                    "metadata": {
                        k: v
                        for k, v in payload.items()
                        if k != "text"
                    },
                }
            )
        return hits

    def collection_stats(self) -> dict[str, Any]:
        try:
            info = self._client.get_collection(self._collection)
            return {
                "collection": self._collection,
                "points_count": info.points_count,
                "vector_size": info.config.params.vectors.size,  # type: ignore[union-attr]
            }
        except Exception as exc:
            return {"collection": self._collection, "error": str(exc)}

    def ping(self) -> bool:
        self._client.get_collections()
        return True
