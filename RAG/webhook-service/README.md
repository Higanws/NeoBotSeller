# Webhook Service — Meta WhatsApp Cloud API

Parte de **RAG/** — punto de entrada HTTP para Meta y el simulador `Streamlit/`.

## Endpoints

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/webhook` | Verificación Meta (`hub.verify_token`) |
| POST | `/webhook` | Mensajes entrantes (Meta o Streamlit) |
| GET | `/health` | Health check |
| GET | `/dev/conversations/{wa_id}` | Solo dev — respuestas para Streamlit |

## Variables

```env
META_VERIFY_TOKEN=neobotseller_dev_token
META_APP_SECRET=
WEBHOOK_DEV_MODE=true
WEBHOOK_DEV_ECHO=false

# Pipeline principal (Meta + Streamlit → RAG API → ia-core)
RAG_SERVICE_URL=http://localhost:8091
```

## Flujo

```text
Meta / Streamlit/  →  POST /webhook  →  RAG/api  →  ia-core  →  respuesta
```

## Inicio

```bash
cd RAG/webhook-service
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn webhook_service.main:app --reload --port 8080
```

## Simulador

Ver `Streamlit/README.md` y `RAG/api/README.md`.
