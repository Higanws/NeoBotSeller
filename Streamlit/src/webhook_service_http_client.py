"""Cliente HTTP hacia RAG/webhook-service."""

from __future__ import annotations

from typing import Any

import httpx

from whatsapp_meta_webhook_payload import build_inbound_text_payload


class WebhookClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def send_text(
        self,
        *,
        wa_id: str,
        text: str,
        contact_name: str,
        phone_number_id: str,
    ) -> tuple[bool, str]:
        payload = build_inbound_text_payload(
            wa_id=wa_id,
            text=text,
            contact_name=contact_name,
            phone_number_id=phone_number_id,
        )
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/webhook", json=payload)
            if response.status_code == 200:
                return True, "Mensaje enviado al webhook"
            return False, f"Error {response.status_code}: {response.text[:200]}"
        except httpx.ConnectError:
            return False, f"No se pudo conectar a {self.base_url}. ¿Está RAG/webhook-service en marcha?"
        except httpx.HTTPError as exc:
            return False, str(exc)

    def fetch_conversation(self, wa_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/dev/conversations/{wa_id}")
            response.raise_for_status()
            return response.json()

    def health(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
