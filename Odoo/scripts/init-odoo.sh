#!/bin/bash
set -euo pipefail

DB_NAME="${ODOO_DB_NAME:-neobotseller}"
ADMIN_PASSWORD="${ODOO_ADMIN_PASSWORD:-admin}"

echo "==> Inicializando Odoo — base de datos: ${DB_NAME}"
echo "==> Módulos: CRM, Inventario (stock), Productos, Ventas"

odoo \
  --config=/etc/odoo/odoo.conf \
  -d "${DB_NAME}" \
  -i base,crm,stock,sale_management,product \
  --stop-after-init \
  --without-demo=all

echo "==> Base de datos creada con CRM e Inventario instalados."
echo "==> Usuario: admin / Contraseña: ${ADMIN_PASSWORD}"
echo "==> Ejecuta: docker compose up -d"
