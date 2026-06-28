from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import fakeredis
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from conversation_service.store import RedisConversationStore  # noqa: E402


@pytest.fixture
def store() -> RedisConversationStore:
    fake = fakeredis.FakeRedis(decode_responses=True)
    with patch("conversation_service.store.redis.from_url", return_value=fake):
        yield RedisConversationStore(
            "redis://fake",
            max_turns=3,
            inactivity_seconds=60,
        )
