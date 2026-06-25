"""Conversation Service — API HTTP de sesiones multi-chat (Redis)."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from conversation_service.config import get_settings
from conversation_service.store import RedisConversationStore

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NeoBotSeller Conversation Service",
    description="Contexto conversacional por wa_id con expiración por inactividad",
    version="0.1.0",
)


class AppendMessageRequest(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str = Field(..., min_length=1)


class MetaPatchRequest(BaseModel):
    meta: dict[str, Any] = Field(default_factory=dict)


@lru_cache
def get_store() -> RedisConversationStore:
    settings = get_settings()
    store = RedisConversationStore(
        settings.redis_url,
        max_turns=settings.conversation_max_turns,
        inactivity_seconds=settings.conversation_ttl_seconds,
    )
    store.ping()
    return store


@app.get("/health")
async def health() -> dict[str, Any]:
    store = get_store()
    return {
        "status": "ok",
        "service": "conversation-service",
        **store.stats(),
    }


@app.get("/v1/stats")
async def stats() -> dict[str, Any]:
    return get_store().stats()


@app.get("/v1/conversations/{wa_id}/messages")
async def get_messages(wa_id: str) -> dict[str, Any]:
    messages = get_store().get_messages(wa_id)
    return {"wa_id": wa_id, "messages": messages, "count": len(messages)}


@app.post("/v1/conversations/{wa_id}/messages")
async def append_message(wa_id: str, body: AppendMessageRequest) -> dict[str, Any]:
    messages = get_store().append(wa_id, body.role, body.content)
    return {"wa_id": wa_id, "messages": messages, "count": len(messages)}


@app.get("/v1/conversations/{wa_id}/meta")
async def get_meta(wa_id: str) -> dict[str, Any]:
    return {"wa_id": wa_id, "meta": get_store().get_meta(wa_id)}


@app.patch("/v1/conversations/{wa_id}/meta")
async def patch_meta(wa_id: str, body: MetaPatchRequest) -> dict[str, Any]:
    meta = get_store().set_meta(wa_id, body.meta)
    return {"wa_id": wa_id, "meta": meta}


@app.delete("/v1/conversations/{wa_id}")
async def clear_conversation(wa_id: str) -> dict[str, str]:
    get_store().clear(wa_id)
    return {"status": "ok", "wa_id": wa_id}
