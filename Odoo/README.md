# Odoo Local — CRM + Inventario

Entorno Odoo 17 local para NeoBotSeller (stock y CRM). Las herramientas se consumen vía **RAG/actions-service** (`:8092`), no MCP.

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

## Integración (XML-RPC → actions-service)

Odoo expone **XML-RPC** para el conector en `connectors/`. **actions-service** importa esa lógica y la expone por HTTP; ia-core y Cursor usan el mismo endpoint.

Variables en `RAG/actions-service/.env`:

```env
ODOO_URL=http://localhost:8069
ODOO_DB_NAME=neobotseller
ODOO_LOGIN=admin
ODOO_USER_PASSWORD=admin
```

Consultar tools (igual que la IA externa):

```bash
curl http://localhost:8092/v1/tools
curl -X POST http://localhost:8092/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"stock_get_product","arguments":{"name":"demo"}}'
```

Ver [RAG/actions-service/README.md](../RAG/actions-service/README.md).

## Estructura

```text
Odoo/
├── docker-compose.yml    # PostgreSQL + Odoo
├── config/odoo.conf      # Configuración Odoo
├── scripts/
│   ├── init-odoo.sh      # Instala CRM + Stock
│   └── seed-demo-data.py # Productos, stock y leads demo
└── connectors/
    ├── stock/            # Inventario
    └── crm/              # CRM
```
