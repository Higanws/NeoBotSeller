"""Almacén de sesiones en Redis — un hilo por wa_id, expira por inactividad."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis

logger = logging.getLogger(__name__)


class RedisConversationStore:
    """
    Claves:
      conversation:{wa_id}       → JSON lista de mensajes
      conversation:{wa_id}:meta  → JSON metadata (contact_name, etc.)
    """

    def __init__(
        self,
        redis_url: str,
        *,
        max_turns: int = 20,
        inactivity_seconds: int = 300,
        key_prefix: str = "conversation",
    ) -> None:
        self._client = redis.from_url(redis_url, decode_responses=True)
        self._max_turns = max_turns
        self._inactivity = inactivity_seconds
        self._prefix = key_prefix

    def _msg_key(self, wa_id: str) -> str:
        return f"{self._prefix}:{wa_id}"

    def _meta_key(self, wa_id: str) -> str:
        return f"{self._prefix}:{wa_id}:meta"

    def _slide_inactivity_ttl(self, wa_id: str) -> None:
        pipe = self._client.pipeline()
        for key in (self._msg_key(wa_id), self._meta_key(wa_id)):
            pipe.expire(key, self._inactivity)
        pipe.execute()

    def get_messages(self, wa_id: str) -> list[dict[str, str]]:
        raw = self._client.get(self._msg_key(wa_id))
        if not raw:
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("JSON inválido en wa_id=%s", wa_id)
            return []

    def append(self, wa_id: str, role: str, content: str) -> list[dict[str, str]]:
        messages = self.get_messages(wa_id)
        messages.append({"role": role, "content": content})
        max_msgs = self._max_turns * 2
        if len(messages) > max_msgs:
            messages = messages[-max_msgs:]
        self._client.setex(
            self._msg_key(wa_id),
            self._inactivity,
            json.dumps(messages, ensure_ascii=False),
        )
        self._slide_inactivity_ttl(wa_id)
        return messages

    def clear(self, wa_id: str) -> None:
        self._client.delete(self._msg_key(wa_id), self._meta_key(wa_id))

    def set_meta(self, wa_id: str, meta: dict[str, Any]) -> dict[str, Any]:
        current = self.get_meta(wa_id)
        current.update(meta)
        self._client.setex(
            self._meta_key(wa_id),
            self._inactivity,
            json.dumps(current, ensure_ascii=False),
        )
        self._slide_inactivity_ttl(wa_id)
        return current

    def get_meta(self, wa_id: str) -> dict[str, Any]:
        raw = self._client.get(self._meta_key(wa_id))
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def stats(self) -> dict[str, Any]:
        keys = list(self._client.scan_iter(match=f"{self._prefix}:*", count=200))
        msg_keys = [k for k in keys if not k.endswith(":meta")]
        return {
            "backend": "redis",
            "conversations": len(msg_keys),
            "inactivity_seconds": self._inactivity,
            "max_turns": self._max_turns,
        }

    def ping(self) -> bool:
        return bool(self._client.ping())
