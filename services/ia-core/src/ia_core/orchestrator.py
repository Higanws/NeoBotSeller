"""Orquestador: contexto Redis + mensaje + tools → el bot decide."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ia_core.config import Settings, get_settings
from ia_core.llm.factory import create_llm_provider
from ia_core.mcp_hub.actions_hub import ActionsHub
from ia_core.mcp_hub.odoo_hub import OdooMcpHub
from ia_core.memory import create_conversation_store
from ia_core.tool_router import ToolRouter

logger = logging.getLogger(__name__)


@dataclass
class ChatResult:
    reply: str
    provider: str
    model: str
    wa_id: str
    usage: dict[str, Any] | None = None
    tools_used: list[str] = field(default_factory=list)


class Orchestrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.llm = create_llm_provider(self.settings)
        service_url = (
            self.settings.conversation_service_url
            if self.settings.conversation_service_enabled
            else None
        )
        self.memory = create_conversation_store(
            service_url=service_url,
            fallback_max_turns=self.settings.conversation_max_turns,
            fallback_inactivity_seconds=self.settings.conversation_ttl_seconds,
        )
        self.odoo_hub = OdooMcpHub(self.settings)
        self.actions_hub = ActionsHub(self.settings)
        self.tool_router = ToolRouter(
            self.llm,
            self.actions_hub,
            self.odoo_hub,
            max_rounds=self.settings.max_tool_rounds,
        )

    def process_message(
        self,
        *,
        wa_id: str,
        text: str,
        contact_name: str | None = None,
        rag_context: list[dict[str, Any]] | None = None,
    ) -> ChatResult:
        if rag_context:
            logger.warning(
                "rag_context en request ignorado — el bot usa rag_search_documents cuando lo necesite"
            )

        logger.info(
            "process wa_id=%s provider=%s chats_active≈%s",
            wa_id,
            self.settings.llm_provider,
            self.memory.stats().get("conversations"),
        )

        if contact_name:
            self.memory.set_meta(wa_id, {"contact_name": contact_name})

        meta = self.memory.get_meta(wa_id)
        display_name = contact_name or meta.get("contact_name")
        history = self.memory.get_messages(wa_id)
        tools = self.tool_router.get_tool_definitions()

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": self._system_prompt(display_name, wa_id, tools),
            },
            *history,
            {"role": "user", "content": text},
        ]

        run_result = self.tool_router.run(messages)
        response = run_result.response

        self.memory.append(wa_id, "user", text)
        self.memory.append(wa_id, "assistant", response.content)

        return ChatResult(
            reply=response.content,
            provider=response.provider,
            model=response.model,
            wa_id=wa_id,
            usage=response.usage,
            tools_used=run_result.tools_used,
        )

    def _system_prompt(
        self,
        contact_name: str | None,
        wa_id: str,
        tools: list[dict[str, Any]],
    ) -> str:
        base = self.settings.system_prompt
        base += (
            f"\n\nSesión activa: wa_id={wa_id}. "
            "El historial de chat precede a este mensaje; úsalo para mantener coherencia."
        )
        if contact_name:
            base += f"\nEl interlocutor se llama {contact_name}."

        if tools:
            names = [
                t.get("function", {}).get("name", "")
                for t in tools
                if t.get("function", {}).get("name")
            ]
            base += (
                "\n\nTienes herramientas disponibles. "
                "Decide tú cuándo invocarlas según la intención del usuario:\n"
                "- Odoo (stock, CRM, clientes): datos operativos del ERP.\n"
                "- rag_search_documents: documentación en PDFs (catálogos, políticas, manuales). "
                "Úsala cuando necesites información que no está en Odoo.\n"
                f"Herramientas: {', '.join(names)}."
            )
        else:
            base += "\n\nNo hay herramientas externas disponibles; responde solo con tu conocimiento."

        return base

    def provider_info(self) -> dict[str, str | bool | Any]:
        mem_stats = self.memory.stats()
        return {
            "provider": self.settings.llm_provider,
            "model": self.settings.llm_model,
            "odoo_mcp_enabled": self.odoo_hub.enabled,
            "actions_service_enabled": self.actions_hub.enabled,
            "memory_backend": mem_stats.get("backend"),
            "active_conversations": mem_stats.get("conversations"),
            "session_inactivity_seconds": mem_stats.get("inactivity_seconds"),
        }
