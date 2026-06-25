"""Cliente HTTP al conversation-service + fallback en memoria local."""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)


class ConversationStore(Protocol):
    def get_messages(self, wa_id: str) -> list[dict[str, str]]: ...
    def append(self, wa_id: str, role: str, content: str) -> None: ...
    def clear(self, wa_id: str) -> None: ...
    def set_meta(self, wa_id: str, meta: dict[str, Any]) -> None: ...
    def get_meta(self, wa_id: str) -> dict[str, Any]: ...
    def stats(self) -> dict[str, Any]: ...


class InMemoryConversationStore:
    """Fallback si conversation-service no está disponible (solo dev)."""

    def __init__(self, max_turns: int = 20, inactivity_seconds: int = 300) -> None:
        from collections import defaultdict, deque

        self._max_turns = max_turns
        self._inactivity = inactivity_seconds
        self._messages: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_turns * 2))
        self._meta: dict[str, dict[str, Any]] = {}
        self._last_activity: dict[str, float] = {}

    def _expire_if_idle(self, wa_id: str) -> None:
        last = self._last_activity.get(wa_id)
        if last is None:
            return
        if time.monotonic() - last > self._inactivity:
            logger.info("Sesión expirada por inactividad wa_id=%s", wa_id)
            self.clear(wa_id)

    def _touch(self, wa_id: str) -> None:
        self._last_activity[wa_id] = time.monotonic()

    def get_messages(self, wa_id: str) -> list[dict[str, str]]:
        self._expire_if_idle(wa_id)
        return list(self._messages.get(wa_id, []))

    def append(self, wa_id: str, role: str, content: str) -> None:
        self._expire_if_idle(wa_id)
        self._messages[wa_id].append({"role": role, "content": content})
        self._touch(wa_id)

    def clear(self, wa_id: str) -> None:
        self._messages.pop(wa_id, None)
        self._meta.pop(wa_id, None)
        self._last_activity.pop(wa_id, None)

    def set_meta(self, wa_id: str, meta: dict[str, Any]) -> None:
        self._expire_if_idle(wa_id)
        self._meta[wa_id] = {**self._meta.get(wa_id, {}), **meta}
        self._touch(wa_id)

    def get_meta(self, wa_id: str) -> dict[str, Any]:
        self._expire_if_idle(wa_id)
        return dict(self._meta.get(wa_id, {}))

    def stats(self) -> dict[str, Any]:
        return {
            "backend": "memory",
            "conversations": len(self._messages),
            "inactivity_seconds": self._inactivity,
        }


class HttpConversationStore:
    """Cliente del servicio Redis/conversation-service (puerto 8093)."""

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    def health_check(self) -> dict[str, Any]:
        response = self._client.get(f"{self._base}/health")
        response.raise_for_status()
        return response.json()

    def get_messages(self, wa_id: str) -> list[dict[str, str]]:
        response = self._client.get(f"{self._base}/v1/conversations/{wa_id}/messages")
        response.raise_for_status()
        return response.json()["messages"]

    def append(self, wa_id: str, role: str, content: str) -> None:
        response = self._client.post(
            f"{self._base}/v1/conversations/{wa_id}/messages",
            json={"role": role, "content": content},
        )
        response.raise_for_status()

    def clear(self, wa_id: str) -> None:
        response = self._client.delete(f"{self._base}/v1/conversations/{wa_id}")
        response.raise_for_status()

    def set_meta(self, wa_id: str, meta: dict[str, Any]) -> None:
        response = self._client.patch(
            f"{self._base}/v1/conversations/{wa_id}/meta",
            json={"meta": meta},
        )
        response.raise_for_status()

    def get_meta(self, wa_id: str) -> dict[str, Any]:
        response = self._client.get(f"{self._base}/v1/conversations/{wa_id}/meta")
        response.raise_for_status()
        return response.json()["meta"]

    def stats(self) -> dict[str, Any]:
        response = self._client.get(f"{self._base}/v1/stats")
        response.raise_for_status()
        data = response.json()
        return {
            "backend": "conversation-service",
            "conversations": data.get("conversations", 0),
            "inactivity_seconds": data.get("inactivity_seconds"),
        }


def create_conversation_store(
    *,
    service_url: str | None,
    fallback_inactivity_seconds: int = 300,
    fallback_max_turns: int = 20,
) -> ConversationStore:
    if service_url:
        try:
            store = HttpConversationStore(service_url)
            info = store.health_check()
            logger.info(
                "Conversation service activo en %s (%s sesiones)",
                service_url,
                info.get("conversations"),
            )
            return store
        except Exception as exc:
            logger.error(
                "Conversation service no disponible (%s), usando memoria local",
                exc,
            )
    return InMemoryConversationStore(
        max_turns=fallback_max_turns,
        inactivity_seconds=fallback_inactivity_seconds,
    )
