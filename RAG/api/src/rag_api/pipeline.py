"""Pipeline: mensaje webhook → ia-core (el bot decide tools y RAG)."""

from __future__ import annotations

import logging

import httpx

from rag_api.config import Settings
from rag_api.message_store import MessageStore, StoredInbound
from rag_api.models import InboundMessageRequest, MessageProcessResponse

logger = logging.getLogger(__name__)


class MessagePipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = MessageStore()

    def process(self, message: InboundMessageRequest) -> MessageProcessResponse:
        logger.info(
            "RAG inbound source=%s wa_id=%s text=%r",
            message.source,
            message.wa_id,
            message.text[:80],
        )

        self.store.append(
            StoredInbound(
                wa_id=message.wa_id,
                text=message.text,
                message_id=message.message_id,
                contact_name=message.contact_name,
                source=message.source,
                meta={
                    "phone_number_id": message.phone_number_id,
                    "timestamp": message.timestamp,
                },
            )
        )

        reply, provider, model, tools_used = self._call_ia_core(
            wa_id=message.wa_id,
            text=message.text,
            contact_name=message.contact_name,
        )

        return MessageProcessResponse(
            wa_id=message.wa_id,
            reply=reply,
            source=message.source,
            rag_chunks_used=1 if "rag_search_documents" in tools_used else 0,
            provider=provider,
            model=model,
            tools_used=tools_used,
        )

    def _call_ia_core(
        self,
        *,
        wa_id: str,
        text: str,
        contact_name: str,
    ) -> tuple[str, str, str, list[str]]:
        url = self.settings.ia_core_url.rstrip("/")
        payload = {
            "wa_id": wa_id,
            "text": text,
            "contact_name": contact_name,
        }
        with httpx.Client(timeout=180.0) as client:
            response = client.post(f"{url}/v1/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        return (
            data.get("reply", ""),
            data.get("provider", ""),
            data.get("model", ""),
            data.get("tools_used", []),
        )
