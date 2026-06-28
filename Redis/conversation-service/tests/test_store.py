from __future__ import annotations

import json

from conversation_service.store import RedisConversationStore


def test_get_messages_empty(store: RedisConversationStore) -> None:
    assert store.get_messages("521111") == []


def test_append_user_and_assistant(store: RedisConversationStore) -> None:
    store.append("521111", "user", "Hola")
    store.append("521111", "assistant", "Hola, ¿en qué ayudo?")

    messages = store.get_messages("521111")
    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "Hola"}
    assert messages[1]["role"] == "assistant"


def test_max_turns_trims_old_messages(store: RedisConversationStore) -> None:
    wa_id = "521222"
    for i in range(10):
        store.append(wa_id, "user", f"u{i}")
        store.append(wa_id, "assistant", f"a{i}")

    messages = store.get_messages(wa_id)
    assert len(messages) == store._max_turns * 2
    assert messages[0]["content"] == "u7"
    assert messages[-1]["content"] == "a9"


def test_meta_roundtrip(store: RedisConversationStore) -> None:
    store.set_meta("521333", {"contact_name": "Ana"})
    store.set_meta("521333", {"locale": "es"})

    meta = store.get_meta("521333")
    assert meta["contact_name"] == "Ana"
    assert meta["locale"] == "es"


def test_clear_removes_messages_and_meta(store: RedisConversationStore) -> None:
    wa_id = "521444"
    store.append(wa_id, "user", "x")
    store.set_meta(wa_id, {"contact_name": "Bob"})
    store.clear(wa_id)

    assert store.get_messages(wa_id) == []
    assert store.get_meta(wa_id) == {}


def test_stats_counts_conversations(store: RedisConversationStore) -> None:
    store.append("a", "user", "1")
    store.append("b", "user", "2")
    stats = store.stats()
    assert stats["backend"] == "redis"
    assert stats["conversations"] == 2


def test_invalid_json_returns_empty(store: RedisConversationStore) -> None:
    wa_id = "bad"
    store._client.set(store._msg_key(wa_id), "not-json")
    assert store.get_messages(wa_id) == []


def test_messages_persisted_as_json(store: RedisConversationStore) -> None:
    store.append("521555", "user", "¿Stock?")
    raw = store._client.get(store._msg_key("521555"))
    assert json.loads(raw)[0]["content"] == "¿Stock?"
