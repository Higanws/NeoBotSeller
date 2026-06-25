# RAG — Plataforma conversacional documental

Bounded context que agrupa la entrada de mensajes, retrieval vectorial y el hub de acciones MCP.

## Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `api/` | 8091 | Mensajes + retrieval → ia-core |
| `webhook-service/` | 8080 | Meta WhatsApp + Streamlit |
| `actions-service/` | 8092 | Hub MCP (Odoo + RAG tools) |
| `embedding-service/` | 8094 | PDF → embeddings → Qdrant |
| `qdrant/` | 6333 | Vector store (Docker) |
| `documents/` | — | Carpeta de PDFs a indexar |

## Flujo RAG documental

```text
RAG/documents/*.pdf
        ↓
embedding-service   POST /v1/ingest
        ↓
Qdrant (vectores)
        ↓
RAG/api retrieval   →  contexto en chat
        ↓
ia-core + actions-service (rag_search_documents)
```

## Flujo conversacional

```text
Streamlit/ / Meta  →  webhook-service  →  RAG/api  →  ia-core
                                              ↓
                                    embedding-service (contexto)
```

## Arranque local

```bash
# 1. Qdrant
cd RAG/qdrant && docker compose up -d

# 2. PDFs
cp catalogo.pdf RAG/documents/

# 3. Embeddings
cd RAG/embedding-service
pip install -r requirements.txt && cp .env.example .env
PYTHONPATH=src uvicorn embedding_service.main:app --port 8094
curl -X POST http://localhost:8094/v1/ingest

# 4. Resto del pipeline
cd RAG/webhook-service && PYTHONPATH=src uvicorn webhook_service.main:app --port 8080
cd RAG/api && PYTHONPATH=src uvicorn rag_api.main:app --port 8091
cd RAG/actions-service && PYTHONPATH=src uvicorn actions_service.main:app --port 8092
cd services/ia-core && PYTHONPATH=src uvicorn ia_core.main:app --port 8090
```

## Servicios externos (raíz)

| Carpeta | Rol |
|---------|-----|
| `Odoo/` | ERP — stock, CRM |
| `Redis/` | Sesiones multi-chat |
| `Streamlit/` | Simulador WhatsApp |
| `services/ia-core/` | Motor LLM |

Ver README de cada subcarpeta.
