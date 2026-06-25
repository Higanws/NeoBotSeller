"""Conector de inventario Odoo para NeoBotSeller."""

from __future__ import annotations

from typing import Any

from connectors.odoo_client import OdooClient

PRODUCT_FIELDS = [
    "id",
    "name",
    "default_code",
    "qty_available",
    "virtual_available",
    "list_price",
    "standard_price",
]


class StockConnector:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def get_product(self, *, sku: str | None = None, name: str | None = None) -> dict[str, Any]:
        if not sku and not name:
            raise ValueError("Indica sku o name para buscar el producto")

        domain: list[Any] = []
        if sku:
            domain.append(("default_code", "=ilike", sku.strip()))
        if name:
            domain.append(("name", "ilike", name.strip()))

        products = self.client.search_read(
            "product.product",
            domain,
            PRODUCT_FIELDS,
            limit=5,
        )
        if not products:
            return {"found": False, "message": "Producto no encontrado", "products": []}

        return {"found": True, "count": len(products), "products": products}

    def check_availability(
        self,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Verifica disponibilidad para una lista de {sku|name, quantity}."""
        results: list[dict[str, Any]] = []

        for item in items:
            sku = item.get("sku")
            name = item.get("name")
            qty_needed = float(item.get("quantity", 1))

            lookup = self.get_product(sku=sku, name=name)
            if not lookup["found"] or not lookup["products"]:
                results.append(
                    {
                        "sku": sku,
                        "name": name,
                        "requested": qty_needed,
                        "available": 0,
                        "sufficient": False,
                        "error": "Producto no encontrado",
                    }
                )
                continue

            product = lookup["products"][0]
            available = float(product.get("qty_available", 0))
            results.append(
                {
                    "product_id": product["id"],
                    "sku": product.get("default_code"),
                    "name": product.get("name"),
                    "requested": qty_needed,
                    "available": available,
                    "sufficient": available >= qty_needed,
                }
            )

        all_ok = all(r.get("sufficient") for r in results)
        return {"all_sufficient": all_ok, "items": results}

    def list_inventory(
        self,
        *,
        warehouse_name: str | None = None,
        low_stock_only: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        domain: list[Any] = [("type", "=", "product")]
        if low_stock_only:
            domain.append(("qty_available", "<=", 10))

        products = self.client.search_read(
            "product.product",
            domain,
            PRODUCT_FIELDS,
            limit=limit,
            order="qty_available asc",
        )

        warehouse_info = None
        if warehouse_name:
            warehouses = self.client.search_read(
                "stock.warehouse",
                [("name", "ilike", warehouse_name)],
                ["id", "name", "lot_stock_id"],
                limit=1,
            )
            if warehouses:
                warehouse_info = warehouses[0]

        return {
            "warehouse": warehouse_info,
            "low_stock_only": low_stock_only,
            "count": len(products),
            "products": products,
        }

    def list_low_stock(self, threshold: float = 10, limit: int = 20) -> dict[str, Any]:
        products = self.client.search_read(
            "product.product",
            [("type", "=", "product"), ("qty_available", "<=", threshold)],
            PRODUCT_FIELDS,
            limit=limit,
            order="qty_available asc",
        )
        return {"threshold": threshold, "count": len(products), "products": products}

    def create_product(
        self,
        *,
        name: str,
        sku: str | None = None,
        list_price: float = 0.0,
        standard_price: float = 0.0,
        initial_qty: float = 0.0,
    ) -> dict[str, Any]:
        """Crea un producto almacenable en Odoo."""
        values: dict[str, Any] = {
            "name": name.strip(),
            "type": "product",
            "list_price": list_price,
            "standard_price": standard_price,
        }
        if sku:
            values["default_code"] = sku.strip()

        product_id = self.client.create("product.product", values)

        if initial_qty > 0:
            tmpl = self.client.search_read(
                "product.product",
                [("id", "=", product_id)],
                ["product_tmpl_id"],
                limit=1,
            )[0]
            tmpl_id = tmpl["product_tmpl_id"][0]
            wizard_id = self.client.execute(
                "stock.change.product.qty",
                "create",
                [
                    {
                        "product_id": product_id,
                        "product_tmpl_id": tmpl_id,
                        "new_quantity": initial_qty,
                    }
                ],
            )
            self.client.execute(
                "stock.change.product.qty",
                "change_product_qty",
                [[wizard_id]],
            )

        product = self.client.search_read(
            "product.product",
            [("id", "=", product_id)],
            PRODUCT_FIELDS,
            limit=1,
        )[0]
        return {
            "success": True,
            "message": f"Producto '{name}' creado",
            "product": product,
            "initial_qty": initial_qty,
        }

    def archive_product(
        self,
        *,
        product_id: int | None = None,
        sku: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Da de baja un producto (active=False). No borra el registro."""
        if product_id:
            products = self.client.search_read(
                "product.product",
                [("id", "=", product_id)],
                PRODUCT_FIELDS + ["active"],
                limit=1,
            )
        else:
            lookup = self.get_product(sku=sku, name=name)
            if not lookup["found"] or not lookup["products"]:
                return {
                    "success": False,
                    "message": "Producto no encontrado para dar de baja",
                }
            products = lookup["products"]

        product = products[0]
        if not product.get("active", True):
            return {
                "success": True,
                "already_archived": True,
                "message": f"El producto '{product.get('name')}' ya estaba dado de baja",
                "product": product,
            }

        self.client.write("product.product", [product["id"]], {"active": False})
        archived = self.client.search_read(
            "product.product",
            [("id", "=", product["id"])],
            PRODUCT_FIELDS + ["active"],
            limit=1,
        )[0]
        return {
            "success": True,
            "message": f"Producto '{archived.get('name')}' dado de baja",
            "product": archived,
        }
