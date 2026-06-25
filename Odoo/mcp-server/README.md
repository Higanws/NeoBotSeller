# NeoBotSeller Odoo MCP

Servidor MCP personalizado para conectar el bot de WhatsApp (ia-core) y Cursor con **Odoo Stock y CRM**.

A diferencia de módulos genéricos del Apps Store, expone solo herramientas de negocio acotadas.

## Herramientas MCP

### Inventario (Stock)

| Tool | Descripción |
|------|-------------|
| `stock_get_product` | Consulta producto por SKU o nombre |
| `stock_check_availability` | Verifica stock para N unidades |
| `stock_list_inventory` | Lista inventario (opcional bajo stock) |
| `stock_list_low_stock` | Productos bajo umbral |

### CRM

| Tool | Descripción |
|------|-------------|
| `crm_search_lead` | Busca leads/oportunidades |
| `crm_get_lead` | Detalle por ID |
| `crm_create_lead` | Crea lead desde conversación |
| `crm_update_stage` | Mueve etapa del pipeline |
| `crm_list_stages` | Lista etapas disponibles |

## Requisitos

- Python 3.10+
- Odoo local en marcha (`docker compose up -d` en `Odoo/`)
- Módulos CRM + Stock instalados

## Instalación

```bash
cd Odoo/mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Variables de entorno

```env
ODOO_URL=http://localhost:8069
ODOO_DB_NAME=neobotseller
ODOO_LOGIN=admin
ODOO_USER_PASSWORD=admin
```

## Ejecutar (stdio MCP)

```bash
source .venv/bin/activate
export ODOO_URL=http://localhost:8069
export ODOO_DB_NAME=neobotseller
export ODOO_LOGIN=admin
export ODOO_USER_PASSWORD=admin
neobotseller-odoo-mcp
```

## Configurar en Cursor

Añade en `.cursor/mcp.json` del proyecto:

```json
{
  "mcpServers": {
    "neobotseller-odoo": {
      "command": "/Users/Personal/Desktop/NeoBotSeller/Odoo/mcp-server/.venv/bin/neobotseller-odoo-mcp",
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB_NAME": "neobotseller",
        "ODOO_LOGIN": "admin",
        "ODOO_USER_PASSWORD": "admin"
      }
    }
  }
}
```

## Prueba rápida (sin MCP)

```bash
cd Odoo/mcp-server
source .venv/bin/activate
PYTHONPATH=src:.. python scripts/smoke_test.py
```

## Estructura

```text
Odoo/
├── connectors/
│   ├── odoo_client.py      # XML-RPC Odoo 17
│   ├── stock/service.py    # Lógica inventario
│   └── crm/service.py      # Lógica CRM
└── mcp-server/
    ├── pyproject.toml
    └── src/neobotseller_odoo_mcp/
        ├── server.py       # Servidor MCP + tools
        └── config.py
```

## Integración ia-core

El `services/ia-core` consumirá este MCP vía **MCP Hub** (stdio o streamable-http). Las operaciones quedan limitadas a las tools definidas — sin acceso ORM genérico.
