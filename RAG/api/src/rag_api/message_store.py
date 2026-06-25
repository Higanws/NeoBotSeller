"""Almacén de mensajes entrantes (dev — sustituible por PostgreSQL)."""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StoredInbound:
    wa_id: str
    text: str
    message_id: str
    contact_name: str
    source: str
    timestamp: float = field(default_factory=time.time)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MessageStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._messages: list[StoredInbound] = []

    def append(self, msg: StoredInbound) -> None:
        with self._lock:
            self._messages.append(msg)

    def list_recent(self, wa_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            items = self._messages
            if wa_id:
                items = [m for m in items if m.wa_id == wa_id]
            return [m.to_dict() for m in items[-limit:]]

    def count(self) -> int:
        with self._lock:
            return len(self._messages)
