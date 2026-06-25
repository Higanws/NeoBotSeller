"""RAG API — recibe mensajes del webhook (Meta / Streamlit)."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag_api.config import get_settings
from rag_api.models import InboundMessageRequest, MessageProcessResponse
from rag_api.pipeline import MessagePipeline
from rag_api.retrieval import RetrievalService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NeoBotSeller RAG API",
    description="Punto de entrada de mensajes desde webhook — retrieval + ia-core",
    version="0.1.0",
)


@lru_cache
def get_pipeline() -> MessagePipeline:
    return MessagePipeline(get_settings())


@app.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    pipeline = get_pipeline()
    return {
        "status": "ok",
        "service": "rag-api",
        "messages_received": pipeline.store.count(),
        "ia_core_url": settings.ia_core_url,
        "rag_retrieval_enabled": settings.rag_enabled,
        "embedding_service_url": settings.embedding_service_url,
        "qdrant_url": settings.qdrant_url,
    }


@app.post("/v1/messages", response_model=MessageProcessResponse)
async def receive_message(message: InboundMessageRequest) -> MessageProcessResponse:
    """
    Recibe mensaje normalizado del webhook.
    Origen: WhatsApp (Meta) o simulador Streamlit — mismo contrato.
    """
    try:
        return get_pipeline().process(message)
    except Exception as exc:
        logger.exception("Error procesando mensaje RAG")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/messages")
async def list_messages(wa_id: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Auditoría dev: mensajes recibidos por RAG."""
    return {
        "count": get_pipeline().store.count(),
        "messages": get_pipeline().store.list_recent(wa_id=wa_id, limit=limit),
    }


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


@app.post("/v1/search")
async def search_documents(body: SearchRequest) -> dict[str, Any]:
    """Búsqueda semántica — usado por actions-service (MCP RAG)."""
    settings = get_settings()
    retrieval = RetrievalService(settings)
    chunks = retrieval.search(body.query)[: body.top_k]
    return {
        "query": body.query,
        "count": len(chunks),
        "chunks": retrieval.format_context(chunks),
    }
