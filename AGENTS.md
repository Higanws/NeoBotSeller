# NeoBotSeller — Guía para agentes

Monorepo de plataforma conversacional WhatsApp con IA agentica, RAG, Odoo y sesiones Redis.

## Mapa del repositorio

```text
NeoBotSeller/
├── AGENTS.md              ← este archivo (visión global)
├── Streamlit/             Simulador WhatsApp (solo consume webhook)
├── RAG/                   Entrada mensajes, actions MCP, embeddings, Qdrant
├── services/ia-core/      Motor LLM + orquestación agentica
├── Odoo/                  ERP local + connectors + mcp-server
├── Redis/                 Sesiones conversacionales (conversation-service)
├── docs/ARCHITECTURE.md   Documento técnico E2E
└── shared/contracts/      Contratos JSON compartidos
```

Cada carpeta raíz es un **bounded context** independiente. Los servicios se comunican por **HTTP**, no importan código entre sí (salvo `RAG/actions-service` → `Odoo/connectors` y `RAG/api`).

## Flujo E2E (implementado)

```text
Streamlit/ o Meta WhatsApp
        ↓ POST /webhook
RAG/webhook-service          :8080
        ↓ POST /v1/messages
RAG/api                      :8091  (auditoría; NO hace RAG pasivo)
        ↓ POST /v1/chat
services/ia-core             :8090
        ├─ historial → Redis/conversation-service :8093
        ├─ tools     → RAG/actions-service        :8092
        │                 ├─ Odoo/connectors (XML-RPC)
        │                 └─ rag_search_documents → embedding-service :8094 → Qdrant :6333
        └─ LLM       → Ollama / OpenAI
        ↓
respuesta → webhook → GET /dev/conversations/{wa_id} → Streamlit
```

## Puertos

| Puerto | Servicio |
|--------|----------|
| 8501 | Streamlit |
| 8080 | RAG/webhook-service |
| 8090 | services/ia-core |
| 8091 | RAG/api |
| 8092 | RAG/actions-service |
| 8093 | Redis/conversation-service |
| 8094 | RAG/embedding-service |
| 6333 | Qdrant (Docker) |
| 6379 | Redis broker (Docker) |
| 8069 | Odoo |
| 11434 | Ollama (local o remoto) |

## Modelo agentico (ia-core)

1. Recupera **historial** de Redis (`user` + `assistant` alternados).
2. Carga **tools** desde actions-service (`GET /v1/tools`).
3. Envía al LLM: `[system] + historial + [mensaje nuevo] + tools`.
4. El **bot decide** qué invocar (Odoo, RAG, o responder directo).
5. Persiste user + respuesta final en Redis (no guarda tool_calls intermedios).

## Tools MCP disponibles

**Stock:** `stock_get_product`, `stock_check_availability`, `stock_list_inventory`, `stock_list_low_stock`, `stock_create_product`, `stock_archive_product`

**CRM:** `crm_search_lead`, `crm_create_lead`, `crm_get_lead`, `crm_update_stage`, `crm_list_stages`, `crm_archive_lead`, `crm_list_advisors`, `crm_create_customer`, `crm_assign_advisor`, `crm_search_customer`

**RAG:** `rag_search_documents` (búsqueda en PDFs indexados en Qdrant)

Definiciones: `Odoo/connectors/tool_definitions.py` + `RAG/api/src/rag_api/tool_definitions.py`  
Ejecutor Odoo: `Odoo/connectors/tool_executor.py`  
Hub: `RAG/actions-service/src/actions_service/orchestrator.py`

## Variables críticas

```env
# webhook
RAG_SERVICE_URL=http://localhost:8091
WEBHOOK_DEV_ECHO=false

# ia-core
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_BASE_URL=http://localhost:11434
ACTIONS_SERVICE_URL=http://localhost:8092
CONVERSATION_SERVICE_URL=http://localhost:8093
MAX_TOOL_ROUNDS=5

# Odoo (actions-service e ia-core fallback)
ODOO_URL=http://localhost:8069
ODOO_DB_NAME=neobotseller
```

## Arranque mínimo (chat sin Odoo/RAG)

Ollama + webhook + RAG/api + ia-core + Streamlit.

## Arranque completo (prueba agentica)

Odoo + Redis + conversation-service + actions-service + (opcional) Qdrant + embedding-service + PDFs en `RAG/documents/` + ingesta `POST /v1/ingest`.

## Convenciones para agentes

- **Nueva tool Odoo:** `Odoo/connectors/` (service + tool_definitions + tool_executor). Reiniciar actions-service.
- **Sesiones chat:** solo vía `Redis/conversation-service`; ia-core usa HTTP, no redis-py directo.
- **UI:** Streamlit solo habla con webhook; no tocar ia-core/Odoo desde UI.
- **RAG documental:** PDFs en `RAG/documents/`; indexar con embedding-service; el bot llama `rag_search_documents`.
- **Commits:** conventional commits (`feat`, `fix`, `chore`); referenciar issues GitLab con `#N`.
- **Python:** 3.10+ (3.12 recomendado). FastAPI + pydantic-settings + uvicorn. `PYTHONPATH=src` al arrancar.

## AGENTS.md por dominio

| Archivo | Contenido |
|---------|-----------|
| `RAG/AGENTS.md` | Pipeline mensajería, actions, embeddings |
| `services/AGENTS.md` | ia-core, LLM, tool router |
| `Odoo/AGENTS.md` | ERP, connectors, MCP |
| `Redis/AGENTS.md` | Sesiones multi-chat |
| `Streamlit/AGENTS.md` | Simulador dev |

## Pendiente / no implementado

- Cola Redis `incoming_messages` en webhook (procesamiento async)
- Persistir tool_calls en Redis
- Ingest-service / retrieval-service separados (lógica en embedding-service + api)
