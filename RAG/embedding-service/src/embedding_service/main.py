"""Embedding Service — ingesta PDF y búsqueda vectorial."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from embedding_service.config import Settings, get_settings
from embedding_service.ingest import IngestPipeline

logger = logging.getLogger(__name__)

_watch_task: asyncio.Task | None = None


async def _watch_documents(pipeline: IngestPipeline, settings: Settings) -> None:
    while True:
        try:
            result = pipeline.ingest_all(force=False)
            if result.chunks_indexed:
                logger.info(
                    "Watch: %s archivos, %s chunks nuevos",
                    result.files_processed,
                    result.chunks_indexed,
                )
        except Exception as exc:
            logger.error("Error en watch de documentos: %s", exc)
        await asyncio.sleep(settings.embedding_watch_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _watch_task
    settings = get_settings()
    if settings.embedding_watch:
        pipeline = get_pipeline()
        _watch_task = asyncio.create_task(_watch_documents(pipeline, settings))
        logger.info(
            "Vigilancia de PDFs activa en %s (cada %ss)",
            settings.documents_dir,
            settings.embedding_watch_interval_seconds,
        )
    yield
    if _watch_task:
        _watch_task.cancel()
        try:
            await _watch_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="NeoBotSeller Embedding Service",
    description="PDF → embeddings → Qdrant",
    version="0.1.0",
    lifespan=lifespan,
)


@lru_cache
def get_pipeline() -> IngestPipeline:
    settings = get_settings()
    pipeline = IngestPipeline(settings)
    pipeline.store.ping()
    return pipeline


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1)


class EmbedResponse(BaseModel):
    vector: list[float]
    dimensions: int


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class IngestRequest(BaseModel):
    force: bool = False


@app.get("/health")
async def health() -> dict[str, Any]:
    pipeline = get_pipeline()
    return {"status": "ok", "service": "embedding-service", **pipeline.stats()}


@app.get("/v1/stats")
async def stats() -> dict[str, Any]:
    return get_pipeline().stats()


@app.get("/v1/documents")
async def list_documents() -> dict[str, Any]:
    pdfs = get_pipeline().list_pdfs()
    return {
        "documents_dir": str(get_settings().documents_dir),
        "files": [p.name for p in pdfs],
        "count": len(pdfs),
    }


@app.post("/v1/ingest")
async def ingest_all(body: IngestRequest | None = None) -> dict[str, Any]:
    """Indexa todos los PDF de RAG/documents/."""
    force = body.force if body else False
    result = get_pipeline().ingest_all(force=force)
    return {
        "files_processed": result.files_processed,
        "chunks_indexed": result.chunks_indexed,
        "errors": result.errors,
    }


@app.post("/v1/ingest/{filename}")
async def ingest_one(filename: str, force: bool = False) -> dict[str, Any]:
    path = get_settings().documents_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"PDF no encontrado: {filename}")
    chunks = get_pipeline().ingest_file(path, force=force)
    return {"filename": filename, "chunks_indexed": chunks}


@app.post("/v1/embed", response_model=EmbedResponse)
async def embed_text(body: EmbedRequest) -> EmbedResponse:
    vector = get_pipeline().embedder.embed_text(body.text)
    return EmbedResponse(vector=vector, dimensions=len(vector))


@app.post("/v1/search")
async def search(body: SearchRequest) -> dict[str, Any]:
    hits = get_pipeline().search(body.query, top_k=body.top_k)
    return {"query": body.query, "count": len(hits), "chunks": hits}
