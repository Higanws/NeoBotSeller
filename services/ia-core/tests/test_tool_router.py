from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from ia_core.llm.base import LLMResponse, ToolCall
from ia_core.mcp_hub.actions_hub import ActionsHub
from ia_core.tool_router import ToolRouter


class SequenceLLM:
    provider_name = "mock"
    model = "mock-model"

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = responses
        self.calls = 0

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> LLMResponse:
        response = self._responses[self.calls]
        self.calls += 1
        return response


def _tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "stock_get_product",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]


def test_run_without_tool_calls_returns_llm_response() -> None:
    llm = SequenceLLM([LLMResponse(content="Hola", provider="mock", model="m")])
    hub = MagicMock(spec=ActionsHub)
    hub.enabled = True
    hub.get_tool_definitions.return_value = _tool_defs()

    result = ToolRouter(llm, hub).run([{"role": "user", "content": "Hola"}])

    assert result.response.content == "Hola"
    assert result.tools_used == []
    assert llm.calls == 1


def test_run_executes_tool_and_returns_final_answer() -> None:
    llm = SequenceLLM(
        [
            LLMResponse(
                content="",
                provider="mock",
                model="m",
                tool_calls=[
                    ToolCall(id="tc1", name="stock_get_product", arguments='{"name":"demo"}')
                ],
            ),
            LLMResponse(content="Hay 5 unidades.", provider="mock", model="m"),
        ]
    )
    hub = MagicMock(spec=ActionsHub)
    hub.enabled = True
    hub.get_tool_definitions.return_value = _tool_defs()
    hub.call_tool.return_value = json.dumps({"qty": 5})

    messages = [{"role": "user", "content": "¿Stock de demo?"}]
    result = ToolRouter(llm, hub).run(messages)

    hub.call_tool.assert_called_once_with("stock_get_product", {"name": "demo"})
    assert result.response.content == "Hay 5 unidades."
    assert result.tools_used == ["stock_get_product"]
    assert messages[-1]["role"] == "tool"
    assert llm.calls == 2


def test_run_tool_error_serializes_error_in_tool_message() -> None:
    llm = SequenceLLM(
        [
            LLMResponse(
                content="",
                provider="mock",
                model="m",
                tool_calls=[ToolCall(id="tc1", name="stock_get_product", arguments="{}")],
            ),
            LLMResponse(content="Falló.", provider="mock", model="m"),
        ]
    )
    hub = MagicMock(spec=ActionsHub)
    hub.enabled = True
    hub.get_tool_definitions.return_value = _tool_defs()
    hub.call_tool.side_effect = RuntimeError("Odoo caído")

    messages = [{"role": "user", "content": "stock"}]
    ToolRouter(llm, hub).run(messages)

    tool_msg = messages[-1]
    assert tool_msg["role"] == "tool"
    assert "Odoo caído" in tool_msg["content"]


def test_get_tool_definitions_empty_when_hub_disabled() -> None:
    hub = MagicMock(spec=ActionsHub)
    hub.enabled = False
    router = ToolRouter(SequenceLLM([]), hub)
    assert router.get_tool_definitions() == []
