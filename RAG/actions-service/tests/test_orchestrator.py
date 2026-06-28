from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx

from actions_service.config import Settings
from actions_service.orchestrator import ActionsOrchestrator


def test_no_backends_unknown_tool_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ODOO_ENABLED", "false")
    monkeypatch.setenv("ODOO_MCP_ENABLED", "false")
    monkeypatch.setenv("RAG_ACTIONS_ENABLED", "false")
    orch = ActionsOrchestrator(Settings())
    assert orch.list_tools() == []

    with pytest.raises(ValueError, match="desconocida"):
        orch.call_tool("stock_get_product", {})


@patch.object(ActionsOrchestrator, "_init_odoo")
@patch.object(ActionsOrchestrator, "_init_rag")
def test_odoo_tool_delegates_to_executor(
    mock_rag: MagicMock,
    mock_odoo: MagicMock,
) -> None:
    orch = ActionsOrchestrator(Settings(odoo_enabled=True, rag_enabled=False))
    orch._stock = MagicMock()
    orch._crm = MagicMock()
    orch._tools = [{"type": "function", "function": {"name": "crm_list_stages"}}]

    with patch("connectors.tool_executor.execute_odoo_tool", return_value=[{"id": 1}]) as exec_mock:
        result = orch.call_tool("crm_list_stages", {})

    exec_mock.assert_called_once()
    assert result == [{"id": 1}]


@respx.mock
@patch.object(ActionsOrchestrator, "_init_odoo")
def test_rag_search_calls_rag_api(mock_odoo: MagicMock) -> None:
    orch = ActionsOrchestrator(
        Settings(odoo_enabled=False, rag_enabled=True, rag_api_url="http://localhost:8091")
    )
    orch._tools = [{"type": "function", "function": {"name": "rag_search_documents"}}]

    respx.post("http://localhost:8091/v1/search").mock(
        return_value=httpx.Response(200, json={"results": [{"text": "chunk"}]})
    )

    result = orch.call_tool("rag_search_documents", {"query": "garantía", "top_k": 3})

    assert result["results"][0]["text"] == "chunk"
    request = respx.calls.last.request
    assert b"garant" in request.content
