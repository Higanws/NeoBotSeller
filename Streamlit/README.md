# Streamlit — Simulador WhatsApp

Servicio **independiente** en la raíz del monorepo (como `Odoo/` y `Redis/`).
Solo consume `RAG/webhook-service` — no accede a ia-core, Odoo ni Redis directamente.

## Requisitos

- Python 3.10+
- `RAG/webhook-service` en marcha (puerto 8080)

## Inicio

```bash
# Terminal 1 — webhook (dentro de RAG/)
cd RAG/webhook-service
source .venv/bin/activate  # o crea venv
PYTHONPATH=src uvicorn webhook_service.main:app --reload --port 8080

# Terminal 2 — simulador
cd Streamlit
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # opcional
streamlit run streamlit_whatsapp_simulator_app.py
```

Abre http://localhost:8501

## Configuración

| Variable / campo | Default | Descripción |
|------------------|---------|-------------|
| `WEBHOOK_SERVICE_URL` | `http://localhost:8080` | URL base del webhook |
| wa_id (sidebar) | `34600111222` | Teléfono simulado del cliente |
| phone_number_id | `SIMULATOR_PHONE_ID` | ID del número de negocio Meta |

## Flujo

```text
Streamlit/  →  POST /webhook  →  RAG/webhook-service
                                      ↓
                               RAG/api  →  ia-core  →  Odoo / Redis
                                      ↓
                               GET /dev/conversations/{wa_id}  →  Streamlit
```

## Estructura

```text
Streamlit/
├── streamlit_whatsapp_simulator_app.py
├── requirements.txt
├── .env.example
└── src/
    ├── whatsapp_meta_webhook_payload.py
    └── webhook_service_http_client.py
```
