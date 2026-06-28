# Actions Service — Hub de herramientas

Parte de **RAG/** — orquesta herramientas para `ia-core`, Cursor y cualquier cliente HTTP:

| Backend | Herramientas |
|---------|--------------|
| **Odoo/** | stock, CRM, clientes, productos |
| **RAG/api** | `rag_search_documents` |

## Flujo

```text
ia-core / Cursor / curl → POST /v1/tools/call → actions-service → Odoo/ | RAG/api
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado + backends activos |
| GET | `/v1/tools` | Lista herramientas (contrato OpenAI) |
| POST | `/v1/tools/call` | Ejecuta herramienta |

Body de `/v1/tools/call`:

```json
{
  "name": "stock_get_product",
  "arguments": { "name": "compu bonita" }
}
```

Respuesta: JSON serializado del resultado (mismo formato que recibe el LLM en ia-core).

## Consultas desde Cursor

No hay servidor MCP stdio. Para consultar Odoo o RAG como lo hace la IA externa, usa HTTP contra `:8092` (terminal, scripts o pide al agente que ejecute curl).

```bash
# Listar tools
curl -s http://localhost:8092/v1/tools | jq .

# Stock
curl -s -X POST http://localhost:8092/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"stock_get_product","arguments":{"name":"demo"}}'

# CRM
curl -s -X POST http://localhost:8092/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"crm_search_lead","arguments":{"query":"demo"}}'

# RAG documental (requiere embedding-service + Qdrant)
curl -s -X POST http://localhost:8092/v1/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"rag_search_documents","arguments":{"query":"política de devoluciones"}}'
```

Requisitos: Odoo en `:8069` para tools ERP; `embedding-service` + Qdrant para RAG.

## Inicio

```bash
cd RAG/actions-service
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
PYTHONPATH=src uvicorn actions_service.main:app --reload --port 8092
```

## ia-core

```env
ACTIONS_SERVICE_URL=http://localhost:8092
```

## Odoo (connectors)

```env
ODOO_URL=http://localhost:8069
ODOO_DB_NAME=neobotseller
ODOO_LOGIN=admin
ODOO_USER_PASSWORD=admin
```
