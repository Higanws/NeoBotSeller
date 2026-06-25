# Services — Motor IA

Solo contiene **ia-core** (orquestador LLM). El resto del pipeline vive en carpetas raíz:

| Carpeta | Contenido |
|---------|-----------|
| `RAG/` | webhook, API mensajes, actions hub |
| `Odoo/` | ERP + MCP |
| `Redis/` | Sesiones conversacionales |
| `Streamlit/` | Simulador WhatsApp |

Ver `RAG/README.md` para el flujo completo.
