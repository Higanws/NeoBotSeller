#!/usr/bin/env python3
"""Prueba rápida de conectores sin MCP (requiere Odoo en marcha)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ODOO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ODOO_ROOT))

from connectors.crm.service import CrmConnector
from connectors.odoo_client import OdooClient, OdooConfig
from connectors.stock.service import StockConnector

from neobotseller_odoo_mcp.config import Settings


def main() -> None:
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

    print("==> stock_get_product (SKU-LAP-001)")
    print(json.dumps(stock.get_product(sku="SKU-LAP-001"), indent=2, ensure_ascii=False))

    print("\n==> crm_search_lead (María)")
    print(json.dumps(crm.search_lead(query="María"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
