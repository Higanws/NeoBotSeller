"""Orquestador de herramientas MCP — Odoo + RAG."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import httpx

from actions_service.config import Settings

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ODOO_ROOT = _REPO_ROOT / "Odoo"
_RAG_ROOT = _REPO_ROOT / "RAG" / "api" / "src"
for p in (_ODOO_ROOT, _RAG_ROOT):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))


class ActionsOrchestrator:
    """Hub único: registra y ejecuta todas las herramientas MCP."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._stock = None
        self._crm = None
        self._tools: list[dict[str, Any]] = []

        if settings.odoo_enabled:
            self._init_odoo()
        if settings.rag_enabled:
            self._init_rag()

    def _init_odoo(self) -> None:
        from connectors.crm.service import CrmConnector
        from connectors.odoo_client import OdooClient, OdooConfig
        from connectors.stock.service import StockConnector
        from connectors.tool_definitions import ODOO_TOOL_DEFINITIONS

        client = OdooClient(
            OdooConfig(
                url=self.settings.odoo_url,
                db=self.settings.odoo_db,
                login=self.settings.odoo_login,
                password=self.settings.odoo_password,
            )
        )
        self._stock = StockConnector(client)
        self._crm = CrmConnector(client)
        self._tools.extend(ODOO_TOOL_DEFINITIONS)
        logger.info("Backend Odoo MCP registrado (%s tools)", len(ODOO_TOOL_DEFINITIONS))

    def _init_rag(self) -> None:
        from rag_api.tool_definitions import RAG_TOOL_DEFINITIONS

        self._tools.extend(RAG_TOOL_DEFINITIONS)
        logger.info("Backend RAG MCP registrado (%s tools)", len(RAG_TOOL_DEFINITIONS))

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        args = arguments or {}
        logger.info("actions call_tool=%s", name)

        if name == "rag_search_documents":
            return self._call_rag_search(args)

        if self._stock and self._crm:
            from connectors.tool_executor import execute_odoo_tool

            return execute_odoo_tool(name, args, stock=self._stock, crm=self._crm)

        raise ValueError(f"Herramienta desconocida o backend deshabilitado: {name}")

    def _call_rag_search(self, args: dict[str, Any]) -> dict[str, Any]:
        url = self.settings.rag_api_url.rstrip("/")
        payload = {"query": args["query"], "top_k": int(args.get("top_k", 5))}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{url}/v1/search", json=payload)
            response.raise_for_status()
            return response.json()

    def call_tool_json(self, name: str, arguments: dict[str, Any]) -> str:
        return json.dumps(self.call_tool(name, arguments), ensure_ascii=False)

    def backends_info(self) -> dict[str, Any]:
        return {
            "odoo_enabled": self._stock is not None,
            "rag_enabled": self.settings.rag_enabled,
            "tools_count": len(self._tools),
        }
