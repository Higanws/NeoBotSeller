from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Permite importar Odoo/connectors desde el monorepo
_ODOO_ROOT = Path(__file__).resolve().parents[3]
if str(_ODOO_ROOT) not in sys.path:
    sys.path.insert(0, str(_ODOO_ROOT))

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from connectors.crm.service import CrmConnector
from connectors.odoo_client import OdooClient, OdooConfig
from connectors.stock.service import StockConnector
from connectors.tool_definitions import ODOO_TOOL_DEFINITIONS
from connectors.tool_executor import execute_odoo_tool
from neobotseller_odoo_mcp.config import Settings

logger = logging.getLogger(__name__)

# Schemas MCP (derivados del contrato compartido)
TOOLS: list[types.Tool] = [
    types.Tool(
        name=t["function"]["name"],
        description=t["function"]["description"],
        inputSchema=t["function"]["parameters"],
    )
    for t in ODOO_TOOL_DEFINITIONS
]


def _json_result(data: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


def create_server() -> Server:
    settings = Settings.from_env()
    client = OdooClient(
        OdooConfig(
            url=settings.odoo_url,
            db=settings.odoo_db,
            login=settings.odoo_login,
            password=settings.odoo_password,
        )
    )
    stock = StockConnector(client)
    crm = CrmConnector(client)
    server = Server("neobotseller-odoo")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        args = arguments or {}
        logger.info("tool=%s args=%s", name, args)
        result = execute_odoo_tool(name, args, stock=stock, crm=crm)
        return _json_result(result)

    return server


async def run_server() -> None:
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    import asyncio

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
