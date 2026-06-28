from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ia_core.config import Settings
from ia_core.orchestrator import Orchestrator


def _tools(*names: str) -> list[dict]:
    return [
        {"type": "function", "function": {"name": n, "parameters": {}}}
        for n in names
    ]


@patch("ia_core.orchestrator.create_llm_provider")
@patch("ia_core.orchestrator.create_conversation_store")
def test_system_prompt_includes_rag_when_tool_available(
    mock_store_factory: MagicMock,
    mock_llm_factory: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_store_factory.return_value = MagicMock()
    mock_llm_factory.return_value = MagicMock()
    monkeypatch.setenv("SYSTEM_PROMPT", "Base prompt.")

    settings = Settings(
        actions_service_url="http://localhost:8092",
    )
    orch = Orchestrator(settings)
    prompt = orch._system_prompt(
        contact_name="María",
        wa_id="521234",
        tools=_tools("stock_get_product", "rag_search_documents"),
    )

    assert "Base prompt." in prompt
    assert "María" in prompt
    assert "521234" in prompt
    assert "rag_search_documents" in prompt
    assert "Qdrant" in prompt or "documentos" in prompt.lower()
    assert "proactiva" in prompt.lower() or "proactivo" in prompt.lower()


@patch("ia_core.orchestrator.create_llm_provider")
@patch("ia_core.orchestrator.create_conversation_store")
def test_system_prompt_omits_rag_block_without_tool(
    mock_store_factory: MagicMock,
    mock_llm_factory: MagicMock,
) -> None:
    mock_store_factory.return_value = MagicMock()
    mock_llm_factory.return_value = MagicMock()

    orch = Orchestrator(Settings(actions_service_url="http://localhost:8092"))
    prompt = orch._system_prompt(
        contact_name=None,
        wa_id="x",
        tools=_tools("stock_get_product"),
    )

    assert "rag_search_documents" not in prompt
    assert "stock_get_product" in prompt
