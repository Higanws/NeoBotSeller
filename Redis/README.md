# Redis — Sesiones conversacionales

Infraestructura Redis + **conversation-service** (API HTTP) para contexto multi-chat.
Mismo patrón que `Odoo/`: carpeta propia en la raíz, consumida por otros servicios vía HTTP.

## Requisitos

- Docker y Docker Compose
- Puerto `6379` (Redis) y `8093` (API) libres

## Inicio rápido

```bash
cd Redis

# 1. Broker Redis
cp .env.example .env
docker compose up -d

# 2. API de sesiones
cd conversation-service
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=src uvicorn conversation_service.main:app --reload --port 8093
```

## Acceso

| Recurso | Valor |
|---------|-------|
| Redis | `redis://localhost:6379/0` |
| API sesiones | http://localhost:8093 |
| Health | `GET /health` |

## Claves Redis

| Clave | Contenido | Expiración |
|-------|-----------|------------|
| `conversation:{wa_id}` | Historial `[{role, content}, ...]` | 5 min sin actividad |
| `conversation:{wa_id}:meta` | `{contact_name, ...}` | 5 min sin actividad |

Cada mensaje renueva el TTL (ventana deslizante).

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado + estadísticas |
| GET | `/v1/conversations/{wa_id}/messages` | Historial del chat |
| POST | `/v1/conversations/{wa_id}/messages` | Añadir mensaje |
| GET | `/v1/conversations/{wa_id}/meta` | Metadata del contacto |
| PATCH | `/v1/conversations/{wa_id}/meta` | Actualizar metadata |
| DELETE | `/v1/conversations/{wa_id}` | Borrar sesión |
| GET | `/v1/stats` | Contadores globales |

## Consumidores

| Servicio | Variable |
|----------|----------|
| `ia-core` | `CONVERSATION_SERVICE_URL=http://localhost:8093` |
| `RAG/webhook-service` | (futuro) cola `incoming_messages` |

```env
# ia-core/.env
CONVERSATION_SERVICE_URL=http://localhost:8093
CONVERSATION_SERVICE_ENABLED=true
```

## Variables conversation-service

```env
REDIS_URL=redis://localhost:6379/0
CONVERSATION_TTL_SECONDS=300
CONVERSATION_MAX_TURNS=20
```

## Comandos útiles

```bash
# Logs Redis
docker compose logs -f redis

# Detener
docker compose down
```
