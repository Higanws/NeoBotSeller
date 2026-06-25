"""Utilidades para payloads Meta WhatsApp Cloud API."""

from __future__ import annotations

import time
import uuid
from typing import Any


def build_inbound_text_payload(
    *,
    wa_id: str,
    text: str,
    contact_name: str = "Usuario Demo",
    phone_number_id: str = "SIMULATOR_PHONE_ID",
    business_account_id: str = "SIMULATOR_WABA_ID",
) -> dict[str, Any]:
    """Construye el JSON que Meta envía al POST /webhook."""
    message_id = f"wamid.sim.{uuid.uuid4().hex[:16]}"
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": business_account_id,
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550000000",
                                "phone_number_id": phone_number_id,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": contact_name},
                                    "wa_id": wa_id,
                                }
                            ],
                            "messages": [
                                {
                                    "from": wa_id,
                                    "id": message_id,
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
