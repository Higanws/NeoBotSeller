#!/usr/bin/env python3
"""
Carga datos de demostración en Odoo local (productos, stock, leads CRM).
Requiere Odoo en marcha y base de datos inicializada.

Uso:
  pip install -r scripts/requirements.txt
  python scripts/seed-demo-data.py
"""

from __future__ import annotations

import os
import sys
import xmlrpc.client

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB_NAME", "neobotseller")
ODOO_USER = os.getenv("ODOO_LOGIN", "admin")
ODOO_PASSWORD = os.getenv("ODOO_USER_PASSWORD", "admin")


def connect():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        print("Error: no se pudo autenticar. Verifica credenciales y que Odoo esté activo.")
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models


def search_or_create(models, uid, model, domain, vals):
    ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD, model, "search", [domain], {"limit": 1}
    )
    if ids:
        return ids[0]
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, "create", [vals])


def seed_products(uid, models):
    print("==> Creando productos de demostración...")

    category_id = search_or_create(
        models,
        uid,
        "product.category",
        [("name", "=", "NeoBotSeller Demo")],
        {"name": "NeoBotSeller Demo"},
    )

    products = [
        {
            "name": "Laptop Pro 15",
            "default_code": "SKU-LAP-001",
            "list_price": 1299.0,
            "standard_price": 890.0,
            "type": "product",
            "categ_id": category_id,
        },
        {
            "name": "Mouse Inalámbrico",
            "default_code": "SKU-MOU-002",
            "list_price": 29.99,
            "standard_price": 12.0,
            "type": "product",
            "categ_id": category_id,
        },
        {
            "name": "Teclado Mecánico",
            "default_code": "SKU-KEY-003",
            "list_price": 89.99,
            "standard_price": 45.0,
            "type": "product",
            "categ_id": category_id,
        },
    ]

    product_ids = []
    for p in products:
        pid = search_or_create(
            models,
            uid,
            "product.product",
            [("default_code", "=", p["default_code"])],
            p,
        )
        product_ids.append(pid)
        print(f"   · {p['name']} ({p['default_code']}) — id={pid}")

    return product_ids


def seed_stock(uid, models, product_ids):
    print("==> Ajustando inventario...")

    quantities = [25, 150, 40]

    for pid, qty in zip(product_ids, quantities):
        product = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "product.product",
            "read",
            [[pid], ["name", "product_tmpl_id"]],
        )[0]

        tmpl_id = product["product_tmpl_id"][0]

        wizard_id = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "stock.change.product.qty",
            "create",
            [
                {
                    "product_id": pid,
                    "product_tmpl_id": tmpl_id,
                    "new_quantity": qty,
                }
            ],
        )

        models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "stock.change.product.qty",
            "change_product_qty",
            [[wizard_id]],
        )

        print(f"   · {product['name']}: {qty} unidades")


def seed_crm(uid, models):
    print("==> Creando leads CRM de demostración...")

    leads = [
        {
            "name": "Interés en Laptop Pro 15",
            "contact_name": "María García",
            "email_from": "maria.garcia@example.com",
            "phone": "+34600111222",
            "description": "Cliente interesada en compra corporativa de laptops.",
            "expected_revenue": 6500.0,
        },
        {
            "name": "Pedido mayorista periféricos",
            "contact_name": "Carlos Ruiz",
            "email_from": "carlos.ruiz@empresa.com",
            "phone": "+34600333444",
            "description": "Solicita cotización de 200 mouses y 50 teclados.",
            "expected_revenue": 12000.0,
        },
        {
            "name": "Seguimiento post-venta",
            "contact_name": "Ana López",
            "email_from": "ana.lopez@cliente.es",
            "phone": "+34600555666",
            "description": "Cliente existente, posible upsell de teclados mecánicos.",
            "expected_revenue": 1800.0,
        },
    ]

    for lead in leads:
        lid = search_or_create(
            models,
            uid,
            "crm.lead",
            [("name", "=", lead["name"])],
            lead,
        )
        print(f"   · {lead['name']} — id={lid}")


def main():
    print(f"==> Conectando a {ODOO_URL} (db={ODOO_DB})...")
    uid, models = connect()
    print(f"==> Autenticado como uid={uid}")

    product_ids = seed_products(uid, models)
    seed_stock(uid, models, product_ids)
    seed_crm(uid, models)

    print("\n==> Datos de demostración cargados correctamente.")
    print(f"    Accede a: {ODOO_URL}")


if __name__ == "__main__":
    main()
