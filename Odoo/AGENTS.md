# Odoo — Guía para agentes

ERP local (Odoo 17) + **connectors XML-RPC**. Las tools se exponen vía `RAG/actions-service` (HTTP).

## Estructura

```text
Odoo/
├── docker-compose.yml      Odoo + PostgreSQL
├── connectors/             Lógica de negocio + contrato de tools
│   ├── odoo_client.py      Cliente XML-RPC
│   ├── tool_definitions.py Contrato OpenAI tools (lista completa)
│   ├── tool_executor.py    Dispatch por nombre de tool
│   ├── stock/service.py    Inventario
│   └── crm/service.py      CRM, clientes, asesores
└── scripts/                seed-demo-data.py, init
```

## Acceso local

| Campo | Valor |
|-------|-----|
| URL | http://localhost:8069 |
| DB | `neobotseller` |
| User | `admin` / `admin` |

```bash
cd Odoo && docker compose up -d
python3 scripts/seed-demo-data.py   # opcional
```

## Tools implementadas

### Stock (`connectors/stock/service.py`)
- `stock_get_product` — consulta por SKU/nombre
- `stock_check_availability` — disponibilidad por items
- `stock_list_inventory` — listado inventario
- `stock_list_low_stock` — stock bajo
- `stock_create_product` — crear producto
- `stock_archive_product` — dar de baja (`active=False`)

### CRM (`connectors/crm/service.py`)
- `crm_search_lead`, `crm_create_lead`, `crm_get_lead`
- `crm_update_stage`, `crm_list_stages`
- `crm_archive_lead` — dar de baja lead
- `crm_list_advisors`, `crm_create_customer`, `crm_assign_advisor`, `crm_search_customer`

## Cómo añadir una tool

1. Método en `stock/service.py` o `crm/service.py`
2. Entrada en `tool_definitions.py` (schema OpenAI)
3. Case en `tool_executor.py`
4. Reiniciar `RAG/actions-service` (ia-core descubre vía GET /v1/tools)

## Consumidores

| Cliente | Cómo accede |
|---------|-------------|
| `RAG/actions-service` | sys.path → `Odoo/connectors` |
| `services/ia-core` | HTTP → actions-service |
| Cursor / dev | Mismo HTTP que ia-core (curl o agente con terminal) |

## Env (actions-service)

```env
ODOO_URL=http://localhost:8069
ODOO_DB_NAME=neobotseller
ODOO_LOGIN=admin
ODOO_USER_PASSWORD=admin
```

## Reglas

- Solo ORM/XML-RPC encapsulado; nunca SQL directo.
- Archivar = `active=False`, no unlink/delete.
- `tool_definitions.py` es la fuente de verdad del contrato de tools.
