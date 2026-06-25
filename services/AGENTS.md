# Services — Guía para agentes

Carpeta del **motor IA**. Solo contiene `ia-core/` hoy.

## ia-core (`ia-core/`)

Orquestador conversacional agentico: historial Redis + LLM + function calling.

### Puerto y arranque

```bash
cd ia-core
cp .env.example .env
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn ia_core.main:app --reload --port 8090
```

### API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado + backend memoria + LLM |
| POST | `/v1/chat` | Procesar mensaje (principal) |
| DELETE | `/v1/conversations/{wa_id}` | Limpiar sesión Redis |

### Módulos

| Módulo | Archivo | Responsabilidad |
|--------|---------|-----------------|
| Orquestador | `orchestrator.py` | Historial + prompt + persistencia |
| Tool router | `tool_router.py` | Bucle LLM ↔ tools (max rounds) |
| Memoria | `memory/redis_store.py` | Cliente HTTP → conversation-service |
| Actions hub | `mcp_hub/actions_hub.py` | Cliente → RAG/actions-service |
| Odoo hub | `mcp_hub/odoo_hub.py` | Fallback directo a connectors |
| LLM | `llm/factory.py` | OpenAI u Ollama |

### Flujo interno `process_message`

1. `get_meta` / `get_messages` desde Redis (historial previo).
2. `get_tool_definitions()` desde actions-service.
3. `[system + history + user]` → `tool_router.run()`.
4. `append(user)` + `append(assistant)` en Redis.

### LLM remoto (Ollama en otra máquina)

```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_BASE_URL=http://192.168.x.x:11434
MAX_TOOL_ROUNDS=5
```

En la máquina Ollama: `export OLLAMA_HOST=0.0.0.0:11434`

Modelo recomendado para tools: **qwen2.5:7b-instruct** o **llama3.1:8b** (3080 10GB).

### Env crítico

```env
CONVERSATION_SERVICE_URL=http://localhost:8093
ACTIONS_SERVICE_URL=http://localhost:8092
ODOO_MCP_ENABLED=true   # fallback si actions cae
```

### Reglas

- No usar redis-py aquí; memoria vía HTTP a `Redis/conversation-service`.
- `rag_context` en POST /v1/chat está **obsoleto**; el bot usa `rag_search_documents`.
- Cambios en tools Odoo → reiniciar actions-service, no ia-core (descubre tools en runtime).
