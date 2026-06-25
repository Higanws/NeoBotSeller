# Streamlit — Guía para agentes

Simulador WhatsApp **independiente** en la raíz del monorepo. Solo para desarrollo; no va a producción con Meta.

## Regla principal

**Solo consume `RAG/webhook-service`.** No llamar a ia-core, Odoo, Redis ni RAG/api directamente.

## Archivos

```text
Streamlit/
├── streamlit_whatsapp_simulator_app.py   App principal
├── src/
│   ├── webhook_service_http_client.py    Cliente HTTP
│   └── whatsapp_meta_webhook_payload.py  Builder payload Meta Cloud API
├── requirements.txt
└── .env.example
```

## Endpoints que usa

| Acción | HTTP |
|--------|------|
| Enviar mensaje | `POST {WEBHOOK_URL}/webhook` |
| Health | `GET {WEBHOOK_URL}/health` |
| Obtener respuestas | `GET {WEBHOOK_URL}/dev/conversations/{wa_id}` |

Default webhook: `http://localhost:8080`

## Arranque

```bash
cd Streamlit
pip install -r requirements.txt
cp .env.example .env
streamlit run streamlit_whatsapp_simulator_app.py
# → http://localhost:8501
```

Requisito previo: `RAG/webhook-service` en :8080 con `WEBHOOK_DEV_ECHO=false` y `RAG_SERVICE_URL` configurado.

## Flujo UI

1. Usuario escribe en chat Streamlit.
2. App construye payload formato Meta Cloud API.
3. POST al webhook.
4. Poll `/dev/conversations/{wa_id}` hasta ver mensaje `outbound`.
5. Muestra respuesta del bot.

## Config sidebar

- `wa_id` — teléfono simulado (identificador de sesión Redis en backend)
- `contact_name`, `phone_number_id`
- URL webhook

## Reglas para agentes

- Cambios de lógica conversacional → **no** en Streamlit; van en ia-core / RAG.
- Streamlit solo cambia UX, payload builder o cliente HTTP.
- No añadir dependencias de Odoo/LLM aquí.
