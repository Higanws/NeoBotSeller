# RAG — Guía para agentes

Bounded context: **entrada de mensajes**, **hub de acciones MCP** y **RAG documental** (PDFs → Qdrant).

## Servicios en esta carpeta

| Carpeta | Puerto | Rol |
|---------|--------|-----|
| `webhook-service/` | 8080 | POST/GET `/webhook` (Meta + Streamlit) |
| `api/` | 8091 | POST `/v1/messages` → delega en ia-core |
| `actions-service/` | 8092 | Hub MCP: Odoo tools + `rag_search_documents` |
| `embedding-service/` | 8094 | PDF → chunks → embeddings → Qdrant |
| `qdrant/` | 6333 | Docker vector store |
| `documents/` | — | Drop zone de PDFs |

## Flujo conversacional

```text
POST /webhook (webhook-service)
  → POST /v1/messages (api) — registra mensaje, NO hace retrieval automático
  → POST /v1/chat (ia-core) — bot agentico decide tools
  → respuesta guardada en webhook store dev
  → Streamlit poll GET /dev/conversations/{wa_id}
```

## Flujo RAG documental (agentico)

El bot invoca `rag_search_documents` cuando lo necesita:

```text
ia-core → actions-service → POST RAG/api/v1/search
                         o embedding-service /v1/search
  → Qdrant
```

Indexación manual:

```bash
cp doc.pdf documents/
curl -X POST http://localhost:8094/v1/ingest
```

## Archivos clave

| Archivo | Qué editar |
|---------|------------|
| `webhook-service/src/webhook_service/main.py` | Webhook Meta, llamada a RAG api |
| `api/src/rag_api/pipeline.py` | Pipeline mensajes → ia-core |
| `api/src/rag_api/retrieval.py` | Búsqueda semántica (vía embedding-service) |
| `api/src/rag_api/tool_definitions.py` | Tool `rag_search_documents` |
| `actions-service/src/actions_service/orchestrator.py` | Registro backends Odoo + RAG |
| `embedding-service/src/embedding_service/ingest.py` | Pipeline PDF → Qdrant |

## Env esencial

```env
# webhook-service/.env
RAG_SERVICE_URL=http://localhost:8091
WEBHOOK_DEV_ECHO=false

# api/.env
IA_CORE_URL=http://localhost:8090
EMBEDDING_SERVICE_URL=http://localhost:8094

# actions-service/.env
ODOO_URL=http://localhost:8069
RAG_API_URL=http://localhost:8091
```

## Arranque

```bash
cd qdrant && docker compose up -d
cd embedding-service && PYTHONPATH=src uvicorn embedding_service.main:app --port 8094
cd actions-service && PYTHONPATH=src uvicorn actions_service.main:app --port 8092
cd api && PYTHONPATH=src uvicorn rag_api.main:app --port 8091
cd webhook-service && PYTHONPATH=src uvicorn webhook_service.main:app --port 8080
```

## Reglas

- No conectar Streamlit directamente a api o ia-core.
- actions-service importa `Odoo/connectors` vía sys.path (`parents[4]` desde orchestrator).
- Añadir tool RAG: `tool_definitions.py` en api + handler en actions orchestrator.
