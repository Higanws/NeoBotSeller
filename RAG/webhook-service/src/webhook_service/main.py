"""Webhook service — entrada WhatsApp Cloud API (Meta)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response

from webhook_service.meta import extract_inbound_messages
from webhook_service.source import detect_message_source
from webhook_service.store import ConversationStore

logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "neobotseller_dev_token")
APP_SECRET = os.getenv("META_APP_SECRET", "")
DEV_MODE = os.getenv("WEBHOOK_DEV_MODE", "true").lower() in ("1", "true", "yes")
DEV_ECHO = os.getenv("WEBHOOK_DEV_ECHO", "true").lower() in ("1", "true", "yes")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "").rstrip("/")
IA_CORE_URL = os.getenv("IA_CORE_URL", "").rstrip("/")  # fallback legacy

store = ConversationStore()

app = FastAPI(
    title="NeoBotSeller Webhook Service",
    description="Recibe eventos de Meta WhatsApp Cloud API",
    version="0.1.0",
)


def _validate_signature(body: bytes, signature: str | None) -> bool:
    if DEV_MODE or not APP_SECRET:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        APP_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature[7:], expected)


def _call_rag(*, wa_id: str, text: str, contact_name: str, message_id: str, source: str, phone_number_id: str, timestamp: str) -> str:
    if not RAG_SERVICE_URL:
        raise RuntimeError("RAG_SERVICE_URL no configurada")
    payload = {
        "wa_id": wa_id,
        "text": text,
        "message_id": message_id,
        "contact_name": contact_name,
        "source": source,
        "phone_number_id": phone_number_id,
        "timestamp": timestamp,
    }
    with httpx.Client(timeout=180.0) as client:
        response = client.post(f"{RAG_SERVICE_URL}/v1/messages", json=payload)
        response.raise_for_status()
        data = response.json()
    return data.get("reply", "")


def _call_ia_core_legacy(*, wa_id: str, text: str, contact_name: str) -> str:
    if not IA_CORE_URL:
        raise RuntimeError("IA_CORE_URL no configurada")
    payload = {"wa_id": wa_id, "text": text, "contact_name": contact_name}
    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{IA_CORE_URL}/v1/chat", json=payload)
        response.raise_for_status()
        data = response.json()
    return data.get("reply", "")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "webhook-service",
        "rag_configured": bool(RAG_SERVICE_URL),
        "ia_core_fallback": bool(IA_CORE_URL),
    }


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
) -> Response:
    """Verificación de suscripción Meta (GET)."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verificado por Meta")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, str]:
    """Recepción de eventos Meta (POST). Mismo endpoint para simulador y producción."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _validate_signature(body, signature):
        raise HTTPException(status_code=401, detail="Firma HMAC inválida")

    payload: dict[str, Any] = await request.json()
    inbound = extract_inbound_messages(payload)

    for msg in inbound:
        source = detect_message_source(msg)
        logger.info("inbound source=%s wa_id=%s text=%r", source, msg.wa_id, msg.text[:80])

        store.append_inbound(
            wa_id=msg.wa_id,
            text=msg.text,
            message_id=msg.message_id,
            contact_name=msg.contact_name,
            meta={
                "phone_number_id": msg.phone_number_id,
                "source": source,
            },
        )

        try:
            if RAG_SERVICE_URL:
                reply = _call_rag(
                    wa_id=msg.wa_id,
                    text=msg.text,
                    contact_name=msg.contact_name,
                    message_id=msg.message_id,
                    source=source,
                    phone_number_id=msg.phone_number_id,
                    timestamp=msg.timestamp,
                )
                store.append_outbound(
                    wa_id=msg.wa_id,
                    text=reply,
                    meta={"source": "rag"},
                )
            elif IA_CORE_URL:
                reply = _call_ia_core_legacy(
                    wa_id=msg.wa_id,
                    text=msg.text,
                    contact_name=msg.contact_name,
                )
                store.append_outbound(
                    wa_id=msg.wa_id,
                    text=reply,
                    meta={"source": "ia-core"},
                )
            elif DEV_MODE and DEV_ECHO:
                store.append_outbound(
                    wa_id=msg.wa_id,
                    text=f"[dev] Recibido: {msg.text}",
                    meta={"source": "dev_echo"},
                )
        except Exception as exc:
            logger.exception("pipeline error")
            store.append_outbound(
                wa_id=msg.wa_id,
                text=f"[error] No se pudo procesar el mensaje: {exc}",
                meta={"source": "pipeline_error"},
            )

    return {"status": "ok"}


@app.get("/dev/conversations/{wa_id}")
async def get_conversation(wa_id: str) -> dict[str, Any]:
    """Solo desarrollo: el simulador Streamlit consulta respuestas aquí."""
    if not DEV_MODE:
        raise HTTPException(status_code=404, detail="Not found")
    return {"wa_id": wa_id, "messages": store.get_conversation(wa_id)}
