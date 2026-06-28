# IA Core — NeoBotSeller

Motor conversacional con **OpenAI** u **Ollama**, configurable vía `.env`.

## Configuración

```bash
cp .env.example .env
```

### Ollama (local, por defecto)

```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

Asegúrate de tener el modelo: `ollama pull llama3.2`

### OpenAI (cloud o LM Studio)

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

## Herramientas (actions-service)

Todas las tools (Odoo + RAG) se cargan y ejecutan vía **RAG/actions-service**:

```env
ACTIONS_SERVICE_URL=http://localhost:8092
MAX_TOOL_ROUNDS=5
```

Levantar actions-service con Odoo en `:8069`. Ver `RAG/actions-service/README.md`.

Herramientas CRM/clientes: `crm_create_customer`, `crm_assign_advisor`, `crm_list_advisors`, `crm_search_customer`, `crm_create_lead`, etc.

Para consultar desde Cursor sin chat: mismos endpoints HTTP (`GET /v1/tools`, `POST /v1/tools/call`).

## Conversation service (Redis/)

Contexto multi-chat vía HTTP — no conectar ia-core directamente a Redis:

```bash
cd Redis && docker compose up -d
cd Redis/conversation-service && PYTHONPATH=src uvicorn conversation_service.main:app --port 8093
```

```env
CONVERSATION_SERVICE_URL=http://localhost:8093
CONVERSATION_SERVICE_ENABLED=true
```

## Inicio

```bash
cd services/ia-core
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=src uvicorn ia_core.main:app --reload --port 8090
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado + proveedor activo |
| GET | `/v1/config` | Configuración (sin secretos) |
| POST | `/v1/chat` | Procesar mensaje |
| DELETE | `/v1/conversations/{wa_id}` | Limpiar historial |

### Ejemplo

```bash
curl -X POST http://localhost:8090/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"wa_id":"34600111222","text":"Hola, ¿tienen laptops?","contact_name":"María"}'
```

## Integración pipeline

En `RAG/webhook-service/.env`:

```env
RAG_SERVICE_URL=http://localhost:8091
WEBHOOK_DEV_ECHO=false
```

Flujo: **webhook → RAG API → ia-core**. Meta y Streamlit usan el mismo `POST /webhook`.

## Estructura

```text
ia-core/
├── .env.example
└── src/ia_core/
    ├── config.py           # Carga .env (pydantic-settings)
    ├── orchestrator.py     # Contexto + LLM + tools
    ├── tool_router.py      # Bucle LLM ↔ actions-service
    ├── memory/
    │   └── redis_store.py    # Cliente HTTP → conversation-service
    ├── main.py
    ├── mcp_hub/
    │   └── actions_hub.py  # Cliente HTTP → RAG/actions-service
    └── llm/
        ├── factory.py      # Selección openai | ollama
        ├── openai_provider.py
        └── ollama_provider.py
```
