"""Almacén en memoria para desarrollo (reemplazable por Redis)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StoredMessage:
    id: str
    wa_id: str
    direction: str  # inbound | outbound
    text: str
    timestamp: float
    contact_name: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConversationStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_wa_id: dict[str, list[StoredMessage]] = {}

    def append_inbound(
        self,
        *,
        wa_id: str,
        text: str,
        message_id: str,
        contact_name: str,
        meta: dict[str, Any] | None = None,
    ) -> StoredMessage:
        msg = StoredMessage(
            id=message_id,
            wa_id=wa_id,
            direction="inbound",
            text=text,
            timestamp=time.time(),
            contact_name=contact_name,
            meta=meta or {},
        )
        with self._lock:
            self._by_wa_id.setdefault(wa_id, []).append(msg)
        return msg

    def append_outbound(self, *, wa_id: str, text: str, meta: dict[str, Any] | None = None) -> StoredMessage:
        msg = StoredMessage(
            id=f"out.{uuid.uuid4().hex[:12]}",
            wa_id=wa_id,
            direction="outbound",
            text=text,
            timestamp=time.time(),
            meta=meta or {},
        )
        with self._lock:
            self._by_wa_id.setdefault(wa_id, []).append(msg)
        return msg

    def get_conversation(self, wa_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [m.to_dict() for m in self._by_wa_id.get(wa_id, [])]
