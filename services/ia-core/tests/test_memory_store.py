from __future__ import annotations

import time
from unittest.mock import patch

from ia_core.memory.redis_store import InMemoryConversationStore, create_conversation_store


def test_in_memory_append_and_get() -> None:
    store = InMemoryConversationStore(max_turns=5, inactivity_seconds=300)
    store.append("wa1", "user", "Hola")
    store.append("wa1", "assistant", "Hola!")

    messages = store.get_messages("wa1")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"


def test_in_memory_meta() -> None:
    store = InMemoryConversationStore()
    store.set_meta("wa1", {"contact_name": "Luis"})
    assert store.get_meta("wa1")["contact_name"] == "Luis"


def test_in_memory_expires_after_inactivity() -> None:
    store = InMemoryConversationStore(inactivity_seconds=1)
    clock = {"t": 100.0}

    def fake_monotonic() -> float:
        return clock["t"]

    with patch("ia_core.memory.redis_store.time.monotonic", side_effect=fake_monotonic):
        store.append("wa1", "user", "x")
        clock["t"] = 103.0
        assert store.get_messages("wa1") == []


def test_create_conversation_store_fallback_when_service_down() -> None:
    store = create_conversation_store(
        service_url="http://localhost:59999",
        fallback_max_turns=10,
    )
    stats = store.stats()
    assert stats["backend"] == "memory"
