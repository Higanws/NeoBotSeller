# Odoo Local — CRM + Inventario

Entorno Odoo 17 local para desarrollo del MCP de NeoBotSeller (stock y CRM).

## Requisitos

- Docker y Docker Compose
- Puerto `8069` libre

## Inicio rápido

```bash
cd Odoo

# 1. Variables de entorno
cp .env.example .env

# 2. Inicializar base de datos con CRM + Inventario (solo la primera vez)
docker compose --profile init run --rm odoo-init

# 3. Levantar servicios
docker compose up -d

# 4. (Opcional) Cargar datos de demostración
python3 scripts/seed-demo-data.py
```

## Acceso

| Recurso | Valor |
|---------|-------|
| URL | http://localhost:8069 |
| Base de datos | `neobotseller` |
| Usuario | `admin` |
| Contraseña | `admin` |

## Módulos instalados

| Módulo | App en Odoo | Uso |
|--------|-------------|-----|
| `crm` | CRM | Leads, oportunidades, pipeline |
| `stock` | Inventario | Almacenes, existencias, movimientos |
| `product` | Productos | Catálogo y SKU |
| `sale_management` | Ventas | Pedidos y cotizaciones |

## Comandos útiles

```bash
# Ver logs
docker compose logs -f odoo

# Detener
docker compose down

# Reiniciar desde cero (borra datos locales)
docker compose down
rm -rf data/
docker compose --profile init run --rm odoo-init
docker compose up -d
```

## API para integración MCP

Odoo expone **XML-RPC** para el conector interno y el servidor MCP de NeoBotSeller.

Variables:

```env
ODOO_URL=http://localhost:8069
ODOO_DB_NAME=neobotseller
ODOO_LOGIN=admin
ODOO_USER_PASSWORD=admin
```

### MCP personalizado (`mcp-server/`)

```bash
cd mcp-server
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
neobotseller-odoo-mcp   # stdio MCP para Cursor / ia-core
```

Herramientas: `stock_get_product`, `stock_check_availability`, `crm_search_lead`, `crm_create_lead`, etc.

Ver [mcp-server/README.md](mcp-server/README.md).

## Estructura

```text
Odoo/
├── docker-compose.yml    # PostgreSQL + Odoo
├── config/odoo.conf      # Configuración Odoo
├── scripts/
│   ├── init-odoo.sh      # Instala CRM + Stock
│   └── seed-demo-data.py # Productos, stock y leads demo
├── connectors/
│   ├── stock/            # (próximo) conector MCP inventario
│   └── crm/              # (próximo) conector MCP CRM
└── mcp-server/           # (próximo) servidor MCP
```
