"""
Simulador de chat WhatsApp — NeoBotSeller

Envía mensajes con el mismo formato que Meta Cloud API a RAG/webhook-service.
Útil para probar el pipeline sin cuenta de WhatsApp Business.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

from webhook_service_http_client import WebhookClient

DEFAULT_WEBHOOK = os.getenv("WEBHOOK_SERVICE_URL", "http://localhost:8080")

st.set_page_config(
    page_title="NeoBotSeller — Simulador WhatsApp",
    page_icon="💬",
    layout="centered",
)

st.title("💬 Simulador WhatsApp")
st.caption(
    "Servicio independiente: solo habla con `RAG/webhook-service` (`POST /webhook`). "
    "Mismo payload que WhatsApp Cloud API."
)

# --- Sidebar ---
with st.sidebar:
    st.header("Configuración")
    webhook_url = st.text_input(
        "URL webhook (RAG/webhook-service)",
        value=st.session_state.get("webhook_url", DEFAULT_WEBHOOK),
        help="Solo endpoint público: POST /webhook",
    )
    wa_id = st.text_input(
        "Teléfono simulado (wa_id)",
        value=st.session_state.get("wa_id", "34600111222"),
        help="Identificador del usuario, formato internacional sin +",
    )
    contact_name = st.text_input("Nombre contacto", value="Usuario Demo")
    phone_number_id = st.text_input(
        "phone_number_id",
        value="SIMULATOR_PHONE_ID",
        help="ID del número de negocio en Meta (simulado en dev)",
    )

    client = WebhookClient(webhook_url)
    online = client.health()
    st.markdown(
        f"**Webhook:** {'🟢 Conectado' if online else '🔴 Sin conexión'}"
    )

    if st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(
        """
**Flujo**
```
Streamlit/  →  RAG/webhook-service  POST /webhook
           →  RAG/api  →  ia-core  →  respuesta
           →  GET /dev/conversations/{wa_id}
```
        """
    )

st.session_state.setdefault("messages", [])
st.session_state.setdefault("last_poll_ts", 0.0)
st.session_state["webhook_url"] = webhook_url
st.session_state["wa_id"] = wa_id

# --- Historial ---
for msg in st.session_state.messages:
    role = msg.get("role", "user")
    with st.chat_message(role):
        st.markdown(msg.get("text", ""))
        if msg.get("meta"):
            with st.expander("Detalle"):
                st.json(msg["meta"])

# --- Envío ---
prompt = st.chat_input("Escribe como si fueras un cliente de WhatsApp…")

if prompt:
    st.session_state.messages.append({"role": "user", "text": prompt})

    with st.spinner("Enviando al webhook…"):
        ok, detail = client.send_text(
            wa_id=wa_id,
            text=prompt,
            contact_name=contact_name,
            phone_number_id=phone_number_id,
        )

    if not ok:
        st.error(detail)
        st.session_state.messages.append(
            {"role": "assistant", "text": f"⚠️ {detail}"}
        )
    else:
        # Poll respuestas del backend (eco dev o ia-core futuro)
        for _ in range(15):
            time.sleep(0.4)
            try:
                conv = client.fetch_conversation(wa_id)
                server_messages = conv.get("messages", [])
                known_ids = {m.get("id") for m in st.session_state.messages if m.get("id")}
                new_bot = [
                    m
                    for m in server_messages
                    if m.get("direction") == "outbound" and m.get("id") not in known_ids
                ]
                for m in new_bot:
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "text": m.get("text", ""),
                            "id": m.get("id"),
                            "meta": m,
                        }
                    )
                if new_bot:
                    break
            except Exception:
                pass
        st.rerun()
