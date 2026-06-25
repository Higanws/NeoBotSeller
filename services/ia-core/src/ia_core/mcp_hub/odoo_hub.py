"""MCP Hub — conexión con herramientas Odoo (mismo contrato que neobotseller-odoo-mcp)."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from ia_core.config import Settings

logger = logging.getLogger(__name__)

_ODOO_ROOT = Path(__file__).resolve().parents[5] / "Odoo"
if _ODOO_ROOT.exists() and str(_ODOO_ROOT) not in sys.path:
    sys.path.insert(0, str(_ODOO_ROOT))


class OdooMcpHub:
    """
    Ejecuta las mismas herramientas que el servidor MCP de Odoo.
    Comparte lógica vía Odoo/connectors (contrato MCP unificado).
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._stock = None
        self._crm = None

        if not settings.odoo_mcp_enabled:
            logger.info("Odoo MCP deshabilitado")
            return

        from connectors.crm.service import CrmConnector
        from connectors.odoo_client import OdooClient, OdooConfig
        from connectors.stock.service import StockConnector
        from connectors.tool_definitions import ODOO_TOOL_DEFINITIONS

        client = OdooClient(
            OdooConfig(
                url=settings.odoo_url,
                db=settings.odoo_db,
                login=settings.odoo_login,
                password=settings.odoo_password,
            )
        )
        self._stock = StockConnector(client)
        self._crm = CrmConnector(client)
        self._tool_definitions = ODOO_TOOL_DEFINITIONS
        logger.info("Odoo MCP Hub conectado a %s (db=%s)", settings.odoo_url, settings.odoo_db)

    @property
    def enabled(self) -> bool:
        return self._stock is not None and self._crm is not None

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        return list(self._tool_definitions)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if not self.enabled:
            raise RuntimeError("Odoo MCP no está habilitado")

        from connectors.tool_executor import execute_odoo_tool

        logger.info("odoo_mcp tool=%s args=%s", name, arguments)
        result = execute_odoo_tool(
            name,
            arguments,
            stock=self._stock,
            crm=self._crm,
        )
        return json.dumps(result, ensure_ascii=False)
