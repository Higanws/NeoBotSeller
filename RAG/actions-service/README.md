# Actions Service — Hub MCP

Parte de **RAG/** — orquesta herramientas MCP para `ia-core`:

| Backend | Herramientas |
|---------|--------------|
| **Odoo/** | stock, CRM, clientes, productos |
| **RAG/api** | `rag_search_documents` |

## Flujo

```text
ia-core → POST /v1/tools/call → actions-service → Odoo/ | RAG/api
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado + backends activos |
| GET | `/v1/tools` | Lista herramientas MCP |
| POST | `/v1/tools/call` | Ejecuta herramienta |

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
