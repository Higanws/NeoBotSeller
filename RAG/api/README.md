# RAG API — entrada de mensajes

Recibe mensajes del `RAG/webhook-service`, los audita y delega en `ia-core`.

**El bot decide** qué hacer: recupera el historial desde Redis, recibe las tools disponibles y elige si consultar Odoo o buscar en embeddings (`rag_search_documents`).

## Flujo

```text
Meta / Streamlit
      ↓
RAG/webhook-service  POST /webhook
      ↓
RAG API            POST /v1/messages
      ↓
ia-core            historial (Redis) + mensaje + tools → LLM
      ↓                    ├── Odoo (stock, CRM…)
      ↓                    └── rag_search_documents → Qdrant
respuesta → webhook → usuario
```

## Inicio

```bash
cd RAG/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=src uvicorn rag_api.main:app --reload --port 8091
```

## Webhook

En `RAG/webhook-service/.env`:

```env
RAG_SERVICE_URL=http://localhost:8091
WEBHOOK_DEV_ECHO=false
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/v1/messages` | Procesar mensaje entrante |
| GET | `/v1/messages` | Auditoría de mensajes recibidos |
| GET | `/health` | Estado del servicio |

### Payload (desde webhook)

```json
{
  "wa_id": "34600111222",
  "text": "¿Tienen laptops en stock?",
  "message_id": "wamid.xxx",
  "contact_name": "María",
  "source": "simulator",
  "phone_number_id": "SIMULATOR_PHONE_ID"
}
```

`source`: `whatsapp` (Meta) | `simulator` (Streamlit)
