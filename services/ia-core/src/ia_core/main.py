"""IA Core — API del motor conversacional NeoBotSeller."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ia_core.config import get_settings
from ia_core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NeoBotSeller IA Core",
    description="Orquestador IA con soporte OpenAI y Ollama",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    wa_id: str = Field(..., description="Identificador del usuario (teléfono WhatsApp)")
    text: str = Field(..., min_length=1)
    contact_name: str | None = None
    rag_context: list[dict[str, Any]] | None = Field(
        default=None,
        deprecated=True,
        description="Obsoleto: el bot invoca rag_search_documents cuando lo necesite",
    )


class ChatResponse(BaseModel):
    wa_id: str
    reply: str
    provider: str
    model: str
    usage: dict[str, Any] | None = None
    tools_used: list[str] = Field(default_factory=list)


@lru_cache
def get_orchestrator() -> Orchestrator:
    return Orchestrator(get_settings())


@app.get("/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    orch = get_orchestrator()
    return {
        "status": "ok",
        "service": "ia-core",
        **orch.provider_info(),
    }


@app.get("/v1/config")
async def config_info() -> dict[str, Any]:
    """Muestra configuración activa (sin secretos)."""
    s = get_settings()
    return {
        "llm_provider": s.llm_provider,
        "llm_model": s.llm_model,
        "llm_temperature": s.llm_temperature,
        "llm_max_tokens": s.llm_max_tokens,
        "openai_base_url": s.openai_base_url,
        "ollama_base_url": s.ollama_base_url,
        "actions_service_url": s.actions_service_url,
        "max_tool_rounds": s.max_tool_rounds,
    }


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = get_orchestrator().process_message(
            wa_id=request.wa_id,
            text=request.text,
            contact_name=request.contact_name,
            rag_context=request.rag_context,
        )
    except Exception as exc:
        logger.exception("Error en chat")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(
        wa_id=result.wa_id,
        reply=result.reply,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        tools_used=result.tools_used,
    )


@app.delete("/v1/conversations/{wa_id}")
async def clear_conversation(wa_id: str) -> dict[str, str]:
    get_orchestrator().memory.clear(wa_id)
    return {"status": "ok", "wa_id": wa_id}
