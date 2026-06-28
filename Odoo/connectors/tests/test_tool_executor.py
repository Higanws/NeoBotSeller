from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from connectors.tool_executor import execute_odoo_tool


def test_stock_get_product_delegates_to_connector() -> None:
    stock = MagicMock()
    stock.get_product.return_value = {"id": 1, "name": "Laptop"}
    crm = MagicMock()

    result = execute_odoo_tool(
        "stock_get_product",
        {"name": "Laptop"},
        stock=stock,
        crm=crm,
    )

    stock.get_product.assert_called_once_with(sku=None, name="Laptop")
    assert result["name"] == "Laptop"


def test_crm_list_stages_delegates() -> None:
    stock = MagicMock()
    crm = MagicMock()
    crm.list_stages.return_value = [{"id": 1, "name": "New"}]

    result = execute_odoo_tool("crm_list_stages", {}, stock=stock, crm=crm)

    crm.list_stages.assert_called_once()
    assert result[0]["name"] == "New"


def test_unknown_tool_raises() -> None:
    with pytest.raises(ValueError, match="desconocida"):
        execute_odoo_tool("not_a_tool", {}, stock=MagicMock(), crm=MagicMock())
