"""Modelos de mensajes entrantes (webhook Meta / Streamlit)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


MessageSource = Literal["whatsapp", "simulator", "unknown"]


class InboundMessageRequest(BaseModel):
    """Mensaje normalizado desde webhook-service."""

    wa_id: str = Field(..., description="Teléfono del usuario (wa_id)")
    text: str = Field(..., min_length=1)
    message_id: str
    contact_name: str = "Unknown"
    source: MessageSource = "unknown"
    phone_number_id: str = ""
    timestamp: str = ""
    raw: dict[str, Any] | None = None


class RagChunk(BaseModel):
    text: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageProcessResponse(BaseModel):
    wa_id: str
    reply: str
    source: MessageSource
    rag_chunks_used: int = 0
    provider: str = ""
    model: str = ""
    tools_used: list[str] = Field(default_factory=list)
