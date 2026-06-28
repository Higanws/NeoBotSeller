from __future__ import annotations

import httpx
import pytest
import respx

from ia_core.config import Settings
from ia_core.mcp_hub.actions_hub import ActionsHub


@respx.mock
def test_get_tool_definitions_caches_response() -> None:
    tools = [{"type": "function", "function": {"name": "stock_get_product"}}]
    respx.get("http://localhost:8092/v1/tools").mock(
        return_value=httpx.Response(200, json={"tools": tools})
    )

    hub = ActionsHub(Settings(actions_service_url="http://localhost:8092"))
    assert hub.get_tool_definitions() == tools
    assert hub.get_tool_definitions() == tools
    assert len(respx.calls) == 1


@respx.mock
def test_call_tool_posts_payload() -> None:
    respx.post("http://localhost:8092/v1/tools/call").mock(
        return_value=httpx.Response(200, json={"result": {"qty": 3}})
    )

    hub = ActionsHub(Settings(actions_service_url="http://localhost:8092"))
    raw = hub.call_tool("stock_get_product", {"name": "demo"})

    assert '"qty": 3' in raw
    request = respx.calls.last.request
    assert request.method == "POST"
    assert b"stock_get_product" in request.content


def test_disabled_when_url_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTIONS_SERVICE_URL", "")
    hub = ActionsHub(Settings())
    assert hub.enabled is False
    assert hub.get_tool_definitions() == []


def test_call_tool_raises_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTIONS_SERVICE_URL", "")
    hub = ActionsHub(Settings())
    with pytest.raises(RuntimeError, match="ACTIONS_SERVICE_URL"):
        hub.call_tool("x", {})
