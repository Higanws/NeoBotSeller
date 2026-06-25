"""Ejecutor de herramientas Odoo — usado por MCP server e ia-core."""

from __future__ import annotations

from typing import Any

from connectors.crm.service import CrmConnector
from connectors.stock.service import StockConnector


def execute_odoo_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    stock: StockConnector,
    crm: CrmConnector,
) -> Any:
    args = arguments or {}

    if name == "stock_get_product":
        return stock.get_product(sku=args.get("sku"), name=args.get("name"))

    if name == "stock_check_availability":
        return stock.check_availability(args["items"])

    if name == "stock_list_inventory":
        return stock.list_inventory(
            warehouse_name=args.get("warehouse_name"),
            low_stock_only=bool(args.get("low_stock_only", False)),
            limit=int(args.get("limit", 20)),
        )

    if name == "stock_list_low_stock":
        return stock.list_low_stock(
            threshold=float(args.get("threshold", 10)),
            limit=int(args.get("limit", 20)),
        )

    if name == "stock_create_product":
        return stock.create_product(
            name=args["name"],
            sku=args.get("sku"),
            list_price=float(args.get("list_price", 0)),
            standard_price=float(args.get("standard_price", 0)),
            initial_qty=float(args.get("initial_qty", 0)),
        )

    if name == "stock_archive_product":
        return stock.archive_product(
            product_id=args.get("product_id"),
            sku=args.get("sku"),
            name=args.get("name"),
        )

    if name == "crm_search_lead":
        return crm.search_lead(
            query=args.get("query"),
            lead_type=args.get("lead_type"),
            limit=int(args.get("limit", 10)),
        )

    if name == "crm_get_lead":
        return crm.get_lead(int(args["lead_id"]))

    if name == "crm_create_lead":
        return crm.create_lead(
            name=args["name"],
            contact_name=args.get("contact_name"),
            email=args.get("email"),
            phone=args.get("phone"),
            description=args.get("description"),
            expected_revenue=args.get("expected_revenue"),
            lead_type=args.get("lead_type", "lead"),
        )

    if name == "crm_update_stage":
        return crm.update_stage(int(args["lead_id"]), args["stage_name"])

    if name == "crm_list_stages":
        return crm.list_stages()

    if name == "crm_list_advisors":
        return crm.list_advisors(query=args.get("query"), limit=int(args.get("limit", 20)))

    if name == "crm_create_customer":
        return crm.create_customer(
            name=args["name"],
            email=args.get("email"),
            phone=args.get("phone"),
            is_company=bool(args.get("is_company", False)),
            comment=args.get("comment"),
            advisor_id=args.get("advisor_id"),
            advisor_login=args.get("advisor_login"),
            advisor_name=args.get("advisor_name"),
        )

    if name == "crm_assign_advisor":
        return crm.assign_advisor(
            partner_id=int(args["partner_id"]),
            advisor_id=args.get("advisor_id"),
            advisor_login=args.get("advisor_login"),
            advisor_name=args.get("advisor_name"),
        )

    if name == "crm_search_customer":
        return crm.search_customer(query=args.get("query"), limit=int(args.get("limit", 10)))

    if name == "crm_archive_lead":
        return crm.archive_lead(
            lead_id=args.get("lead_id"),
            query=args.get("query"),
        )

    raise ValueError(f"Herramienta Odoo desconocida: {name}")
