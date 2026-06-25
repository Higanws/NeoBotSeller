"""Enrutador de herramientas — bucle LLM + actions-service (MCP hub)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from ia_core.llm.base import LLMProvider, LLMResponse
from ia_core.mcp_hub.actions_hub import ActionsHub
from ia_core.mcp_hub.odoo_hub import OdooMcpHub

logger = logging.getLogger(__name__)


@dataclass
class ToolRunResult:
    response: LLMResponse
    tools_used: list[str] = field(default_factory=list)


class ToolRouter:
    def __init__(
        self,
        llm: LLMProvider,
        actions_hub: ActionsHub,
        odoo_hub: OdooMcpHub,
        max_rounds: int = 3,
    ) -> None:
        self.llm = llm
        self.actions_hub = actions_hub
        self.odoo_hub = odoo_hub
        self.max_rounds = max_rounds

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        return self._get_tools() or []

    def _get_tools(self) -> list[dict[str, Any]] | None:
        if self.actions_hub.enabled:
            tools = self.actions_hub.get_tool_definitions()
            return tools or None
        if self.odoo_hub.enabled:
            return self.odoo_hub.get_tool_definitions()
        return None

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        if self.actions_hub.enabled:
            return self.actions_hub.call_tool(name, args)
        return self.odoo_hub.call_tool(name, args)

    def run(self, messages: list[dict[str, Any]]) -> ToolRunResult:
        tools = self._get_tools()
        last_response: LLMResponse | None = None
        tools_used: list[str] = []

        for round_idx in range(self.max_rounds):
            last_response = self.llm.chat(messages, tools=tools)
            if not last_response.has_tool_calls:
                return ToolRunResult(response=last_response, tools_used=tools_used)

            logger.info("tool round %s — %s llamadas", round_idx + 1, len(last_response.tool_calls))

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": last_response.content or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": tc.arguments},
                    }
                    for tc in last_response.tool_calls
                ],
            }
            messages.append(assistant_msg)

            for tc in last_response.tool_calls:
                tools_used.append(tc.name)
                try:
                    args = json.loads(tc.arguments) if tc.arguments else {}
                    result = self._execute_tool(tc.name, args)
                except Exception as exc:
                    logger.exception("tool error %s", tc.name)
                    result = json.dumps({"error": str(exc)}, ensure_ascii=False)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": result,
                    }
                )

        fallback = last_response or LLMResponse(
            content="No pude completar la solicitud.",
            provider=self.llm.provider_name,
            model=self.llm.model,
        )
        return ToolRunResult(response=fallback, tools_used=tools_used)
