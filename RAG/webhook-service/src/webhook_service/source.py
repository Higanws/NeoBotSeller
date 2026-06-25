"""Detección de origen del mensaje."""

from __future__ import annotations

from webhook_service.meta import InboundMessage

SIMULATOR_PHONE_IDS = {"SIMULATOR_PHONE_ID", "simulator"}


def detect_message_source(msg: InboundMessage) -> str:
    if msg.phone_number_id in SIMULATOR_PHONE_IDS:
        return "simulator"
    if msg.message_id.startswith("wamid.sim."):
        return "simulator"
    return "whatsapp"
