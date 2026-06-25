"""Parseo de payloads Meta WhatsApp Cloud API."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class InboundMessage:
    wa_id: str
    message_id: str
    text: str
    contact_name: str
    phone_number_id: str
    timestamp: str
    raw: dict[str, Any]


def extract_inbound_messages(payload: dict[str, Any]) -> list[InboundMessage]:
    messages: list[InboundMessage] = []

    if payload.get("object") != "whatsapp_business_account":
        return messages

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            contacts = {
                c.get("wa_id"): c.get("profile", {}).get("name", "Unknown")
                for c in value.get("contacts", [])
            }
            phone_number_id = value.get("metadata", {}).get("phone_number_id", "")

            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                body = msg.get("text", {}).get("body", "")
                wa_id = msg.get("from", "")
                messages.append(
                    InboundMessage(
                        wa_id=wa_id,
                        message_id=msg.get("id", str(uuid.uuid4())),
                        text=body,
                        contact_name=contacts.get(wa_id, "Unknown"),
                        phone_number_id=phone_number_id,
                        timestamp=msg.get("timestamp", ""),
                        raw=msg,
                    )
                )

    return messages
