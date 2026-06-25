# Redis — Guía para agentes

Sesiones conversacionales **multi-chat** (un hilo por `wa_id`). Patrón igual que Odoo: carpeta raíz + servicio HTTP consumible.

## Estructura

```text
Redis/
├── docker-compose.yml           Broker Redis 7 (:6379)
└── conversation-service/        API HTTP (:8093)
    └── src/conversation_service/
        ├── main.py              FastAPI
        └── store.py             RedisConversationStore
```

## Consumidor

**Solo `services/ia-core`** vía HTTP (`memory/redis_store.py` → `HttpConversationStore`).

No conectar otros servicios directamente a Redis.

## Qué se guarda

Clave `conversation:{wa_id}` — JSON:

```json
[
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]
```

- Se guardan **mensajes user + assistant** (respuestas del bot).
- **No** se persisten tool_calls ni resultados de tools.
- Meta en `conversation:{wa_id}:meta` (`contact_name`, etc.).
- Expiración: **5 min inactividad** (TTL deslizante; cada mensaje renueva).

## API conversation-service

| Método | Ruta |
|--------|------|
| GET | `/health` |
| GET | `/v1/conversations/{wa_id}/messages` |
| POST | `/v1/conversations/{wa_id}/messages` |
| PATCH | `/v1/conversations/{wa_id}/meta` |
| DELETE | `/v1/conversations/{wa_id}` |

## Arranque

```bash
cd Redis && docker compose up -d
cd conversation-service
pip install -r requirements.txt && cp .env.example .env
PYTHONPATH=src uvicorn conversation_service.main:app --port 8093
```

## Env

```env
# conversation-service
REDIS_URL=redis://localhost:6379/0
CONVERSATION_TTL_SECONDS=300
CONVERSATION_MAX_TURNS=20

# ia-core
CONVERSATION_SERVICE_URL=http://localhost:8093
CONVERSATION_SERVICE_ENABLED=true
```

## Fallback

Si conversation-service no responde, ia-core usa `InMemoryConversationStore` (solo dev, se pierde al reiniciar).

## Pendiente

- Cola `incoming_messages` en webhook (futuro)
- Persistir historial de tool calls para auditoría
