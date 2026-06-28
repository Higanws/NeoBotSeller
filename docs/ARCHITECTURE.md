# Documento Técnico E2E — WhatsApp IA Bot Platform v1.0

> Plataforma conversacional para WhatsApp con IA, RAG, MCP, integración Odoo y despliegue en Docker Compose / Kubernetes.

---

## 1. Resumen Ejecutivo

La solución consiste en una plataforma conversacional para WhatsApp capaz de:

- Recibir mensajes desde **WhatsApp Cloud API**.
- Procesarlos mediante un **motor de IA** desacoplado.
- Consultar documentación corporativa mediante **RAG** (servicio independiente).
- Ejecutar herramientas externas vía **MCP**, incluyendo integración con **Odoo** (stock y CRM).
- Persistir historial de conversaciones y auditoría.
- Ofrecer **panel de administración y UX** en un servicio dedicado.
- Escalar desde un entorno local hasta **Kubernetes**.

La arquitectura está organizada como **monorepo de microservicios**: cada carpeta raíz representa un dominio autónomo con su propio ciclo de vida, contenedor y despliegue.

---

## 2. Objetivos

### Funcionales

| Objetivo | Responsable |
|----------|-------------|
| Atender conversaciones vía WhatsApp | `RAG/webhook-service` + `services/ia-core` |
| Mantener contexto de conversación | `Redis/conversation-service` |
| Consultar documentación interna | `RAG/api` |
| Gestionar stock y CRM en Odoo | `Odoo/` (MCP) |
| Acceder a otros sistemas externos | `RAG/actions-service` + `ia-core` |
| Registrar auditoría completa | PostgreSQL |
| Soportar múltiples proveedores LLM | `services/ia-core` |
| Simulador WhatsApp (dev) | `Streamlit/` |
| Administración (futuro) | `platform-admin/` u otra UI en raíz |

### No Funcionales

- Respuesta < 5 segundos (P95).
- Escalabilidad horizontal por servicio.
- Arquitectura cloud-ready.
- Alta extensibilidad (nuevos MCP sin tocar el core).
- Independencia del proveedor LLM.

---

## 3. Arquitectura General

```text
Usuario
    │
    ▼
WhatsApp
    │
    ▼
Meta Cloud API
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  RAG/webhook-service                                    │
│  Valida HMAC · Normaliza · Publica en cola              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
                    Redis Queue
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  services/ia-core                                       │
│  ┌─────────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ │
│  │ Orchestrator│ │Tool Router│ │ MCP Hub │ │LLM Layer │ │
│  └─────────────┘ └──────────┘ └────┬────┘ └──────────┘ │
└────────────────────────────────────┼────────────────────┘
         │              │            │
         ▼              ▼            ▼
   PostgreSQL        RAG/api     RAG/actions-service
   (historial)      (Qdrant)    (Odoo stock · CRM · RAG tools)
                         │
                         ▼
                  Otros backends HTTP
                         │
                         ▼
                  Meta Cloud API → Usuario

┌─────────────────────────────────────────────────────────┐
│  Streamlit/  (dev, solo consume webhook)                │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Estructura del Monorepo

```text
NeoBotSeller/
├── docs/
│   └── ARCHITECTURE.md
├── whatsapp-ia-architecture.html
│
├── Streamlit/                   ← Simulador WhatsApp (solo → webhook)
│
├── services/
│   └── ia-core/                 ← Orquestador LLM
│
├── RAG/                         ← Pipeline mensajería + RAG + actions
│   ├── webhook-service/
│   ├── actions-service/
│   ├── api/
│   ├── ingest-service/
│   ├── embedding-service/
│   └── retrieval-service/
│
├── Odoo/
│   └── connectors/
│
├── Redis/
│   └── conversation-service/
│
├── infra/
│   └── ...
│
└── shared/
    └── contracts/
```

### Principio de desacoplamiento

Cada carpeta raíz (`RAG/`, `Odoo/`, `Redis/`, `Streamlit/`, `services/ia-core`) es un **bounded context** independiente:

- Tiene su propio `Dockerfile` (futuro).
- Se comunica con el resto solo por **HTTP/gRPC** o **protocolo MCP**.
- Puede desplegarse, escalar y versionarse por separado.
- No importa código interno de otros servicios; solo consume contratos en `shared/contracts/`.

---

## 5. Componentes

### 5.1 WhatsApp Cloud API

**Responsabilidad:** Canal oficial de comunicación con WhatsApp.

| Operación | Descripción |
|-----------|-------------|
| Recepción | Webhooks de mensajes entrantes |
| Envío | Respuestas al usuario vía Graph API |
| Suscripción | Verificación GET del webhook |

**Dependencias:** Meta Developers, Meta Graph API.

---

### 5.2 Webhook Service — `RAG/webhook-service/`

**Tecnología:** Node.js o FastAPI.

**Responsabilidades:**

- Recibir eventos de Meta.
- Validar firma `X-Hub-Signature-256` (HMAC SHA256).
- Normalizar mensajes a un contrato interno (`shared/contracts/`).
- Publicar en cola Redis `incoming_messages`.
- Responder 200 OK de forma inmediata (procesamiento asíncrono).

**Endpoints:**

```http
GET  /webhook    # Verificación de suscripción Meta
POST /webhook    # Recepción de eventos
```

---

### 5.3 Redis

**Uso compartido entre servicios:**

| Clave | Propósito | TTL |
|-------|-----------|-----|
| `conversation:{phone}` | Cache de sesión / contexto corto | 24 h |
| `rate:{phone}` | Rate limiting por usuario | configurable |
| `incoming_messages` | Cola de mensajes entrantes | — |

---

### 5.4 IA Core — `services/ia-core/`

**Tecnología:** Python + FastAPI.

**Módulos internos:**

| Módulo | Función |
|--------|---------|
| **Orchestrator** | Coordina prompt, RAG, MCP, herramientas y respuesta final |
| **Tool Router** | Decide: ¿responder? ¿buscar contexto? ¿invocar herramienta? |
| **MCP Hub** | Gestiona conexiones a servidores MCP (Odoo, filesystem, search…) |
| **LLM Layer** | Abstracción multi-proveedor (OpenAI, Ollama, Claude) |

**Dependencias externas:**

- `RAG/api` — búsqueda semántica.
- `RAG/actions-service` — hub HTTP de tools (Odoo stock/CRM + RAG).
- PostgreSQL — persistencia.
- Redis — cola y cache.
- Meta Graph API — envío de respuestas.

---

### 5.5 RAG — `RAG/`

Microservicio autónomo de Retrieval-Augmented Generation, dividido en sub-servicios desplegables.

#### Pipeline de ingesta

```text
Documento (PDF · Excel · CSV · HTML · Web)
    │
    ▼
Loader          →  RAG/ingest-service/src/loaders/
    │
    ▼
Chunker         →  RAG/ingest-service/src/chunker/
    │
    ▼
Embedding       →  RAG/embedding-service/
    │
    ▼
Qdrant          →  colección vectorial
```

#### Pipeline de retrieval

```text
Pregunta usuario
    │
    ▼
Embedding       →  RAG/embedding-service/
    │
    ▼
Similarity Search (Top-K)  →  RAG/retrieval-service/
    │
    ▼
Chunks + metadata → ia-core (prompt augmentation)
```

#### API expuesta (`RAG/api/`)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/ingest` | POST | Ingestar documento |
| `/search` | POST | Búsqueda semántica |
| `/collections` | GET/POST/DELETE | Gestión de colecciones |
| `/health` | GET | Health check |

#### Modelo de dato en Qdrant

```json
{
  "id": "chunk_001",
  "text": "...",
  "metadata": {
    "source": "manual.pdf",
    "page": 10
  },
  "vector": []
}
```

---

### 5.6 Odoo — `Odoo/`

Integración con **Odoo ERP** expuesta vía **RAG/actions-service** (HTTP) para que el LLM invoque herramientas de negocio.

#### Arquitectura interna

```text
ia-core (Actions Hub HTTP)
    │
    ▼
RAG/actions-service/      ← GET /v1/tools · POST /v1/tools/call
    │
    ├── Odoo/connectors/stock/
    │       ├── get_product_stock
    │       ├── check_availability
    │       └── list_low_stock
    │
    └── Odoo/connectors/crm/
            ├── search_lead
            ├── create_opportunity
            ├── get_contact
            └── update_pipeline_stage
```

#### Herramientas MCP previstas

| Herramienta | Dominio | Descripción |
|-------------|---------|-------------|
| `stock_get_product` | Stock | Consultar existencias por SKU/nombre |
| `stock_check_availability` | Stock | Verificar disponibilidad para pedido |
| `stock_list_warehouse` | Stock | Inventario por almacén |
| `crm_search_lead` | CRM | Buscar leads por criterio |
| `crm_create_lead` | CRM | Crear lead desde conversación |
| `crm_get_opportunity` | CRM | Detalle de oportunidad |
| `crm_update_stage` | CRM | Mover oportunidad en pipeline |

#### Seguridad Odoo

- Autenticación vía API key / OAuth2 de Odoo.
- Whitelist de modelos y operaciones permitidas.
- Sin SQL directo; solo ORM/XML-RPC/JSON-RPC encapsulado.
- Logs de auditoría en `tool_logs` (PostgreSQL).

---

### 5.7 UI — `Streamlit/`

Simulador de chat en **Streamlit**, servicio independiente en la raíz (como `Odoo/` y `Redis/`).

| Función | Descripción |
|---------|-------------|
| Chat simulado | Interfaz tipo WhatsApp para testers |
| Payload Meta | `POST /webhook` con el mismo JSON que Cloud API |
| Polling respuestas | `GET /dev/conversations/{wa_id}` |

**Comunicación:** solo con `RAG/webhook-service`. No accede a Odoo, ia-core ni Redis directamente.

**Panel admin (futuro):** carpeta aparte en raíz cuando haga falta (p. ej. `platform-admin-web/`).

---

## 6. Capa de herramientas (actions-service)

### Objetivo

Permitir que el LLM interactúe con Odoo y RAG de forma segura vía un único hub HTTP.

### Hub

| Componente | Ubicación | Acceso |
|----------|-----------|--------|
| **Actions service** | `RAG/actions-service/` | Odoo stock + CRM + `rag_search_documents` |

Cursor y desarrollo usan los mismos endpoints HTTP que ia-core (no MCP stdio).

### Flujo de invocación

```text
LLM decide usar herramienta
    │
    ▼
Tool Router (ia-core)
    │
    ▼
MCP Hub → selecciona servidor
    │
    ▼
Ejecuta tool con args validados
    │
    ▼
Resultado → contexto LLM → respuesta final
    │
    ▼
tool_logs (PostgreSQL)
```

---

## 7. Capa LLM

### Proveedores soportados

| Tipo | Proveedor | Modelos |
|------|-----------|---------|
| Local | Ollama | Llama 3.x, Mistral |
| Cloud | OpenAI | GPT-4o, gpt-4o-mini |
| Cloud | Anthropic | Claude Sonnet |

### Configuración

Archivo `.env` en `services/ia-core/`:

```env
# Proveedor: openai | ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 8. Persistencia — PostgreSQL

### Tablas

```sql
-- users
id, phone, name, created_at

-- conversations
id, user_id, created_at

-- messages
id, conversation_id, role, content, timestamp

-- tool_logs
id, tool_name, request, response, duration_ms, created_at
```

---

## 9. Flujo End-to-End

### Recepción

```text
Usuario → WhatsApp → Meta Cloud API → webhook-service
```

### Procesamiento

```text
webhook-service: valida firma → publica en Redis
ia-core: consume cola → recupera contexto → RAG search → MCP tools → LLM
```

### Respuesta

```text
LLM → respuesta final → Meta Graph API → WhatsApp → Usuario
```

### Auditoría

```text
Mensaje + tool calls → PostgreSQL (messages, tool_logs)
```

---

## 10. Seguridad

| Área | Medida |
|------|--------|
| Secretos | `.env` / Docker Secrets / Kubernetes Secrets |
| Webhook | HMAC SHA256 (`X-Hub-Signature-256`) |
| Rate limiting | Redis `rate:{phone}` |
| MCP | Tool whitelisting + aislamiento por servidor |
| Odoo | Solo operaciones permitidas, sin acceso directo a DB |
| Tokens | WhatsApp Token, OpenAI Key, Brave API Key, Odoo API Key, Database URL |

---

## 11. Observabilidad — `infra/observability/`

### Logs

JSON structured logs en todos los servicios.

### Métricas (Prometheus)

| Métrica | Servicio |
|---------|----------|
| `request_count` | webhook-service |
| `request_duration` | todos |
| `llm_tokens` | ia-core |
| `tool_calls` | ia-core, Odoo |
| `rag_hits` | RAG |

### Dashboards (Grafana)

- Conversaciones activas.
- Latencia end-to-end.
- Costos LLM por modelo.
- Uso de herramientas MCP (Odoo stock vs CRM).

---

## 12. Despliegue

### Docker Compose — `infra/docker-compose/`

Servicios previstos:

```text
webhook-service
ia-core
rag-api
odoo-mcp
platform-api
platform-web
redis
postgres
qdrant
```

### Kubernetes — `infra/kubernetes/manifests/`

| Recurso | Contenido |
|---------|-----------|
| Deployments | Uno por microservicio |
| ConfigMaps | `app-config`, `mcp-config` |
| Secrets | `openai-secret`, `meta-secret`, `db-secret`, `odoo-secret` |
| Ingress | `webhook.company.com`, `api.company.com`, `admin.company.com` |

---

## 13. Escalabilidad

| Componente | Estrategia |
|------------|------------|
| webhook-service | 1 → N pods (stateless) |
| ia-core | 1 → N workers (cola Redis) |
| RAG/api | 1 → N pods (ingesta y búsqueda) |
| RAG/actions-service | 1 → N pods (stateless) |
| Streamlit/ | 1 instancia local (dev) |
| Redis | Redis Sentinel / Cluster |
| PostgreSQL | Primary + Read Replicas |
| Qdrant | Cluster Mode |

---

## 14. Contratos entre servicios — `shared/contracts/`

Los servicios se comunican exclusivamente mediante contratos versionados:

- **Eventos de mensaje** — webhook → Redis → ia-core.
- **RAG API** — OpenAPI spec en `shared/contracts/rag-api.yaml`.
- **Odoo tools** — Schemas en `Odoo/connectors/tool_definitions.py`.
- **Platform admin API** (futuro) — OpenAPI en `shared/contracts/platform-api.yaml`.

---

## 15. Roadmap de Implementación

### Fase 1 — Fundación

- [ ] `RAG/webhook-service` — webhook WhatsApp
- [ ] `services/ia-core` — orquestador básico + OpenAI
- [ ] PostgreSQL + Redis en `infra/docker-compose/`
- [ ] Flujo E2E sin RAG ni MCP

### Fase 2 — RAG

- [ ] `RAG/ingest-service` — loaders y chunking
- [ ] `RAG/embedding-service` + Qdrant
- [ ] `RAG/retrieval-service` — búsqueda semántica
- [ ] `RAG/api` — API unificada
- [ ] Integración ia-core ↔ RAG

### Fase 3 — Tools y Odoo

- [x] `RAG/actions-service` — hub HTTP de herramientas
- [x] `Odoo/connectors/stock` — herramientas de inventario
- [x] `Odoo/connectors/crm` — herramientas CRM
- [x] Actions Hub en ia-core

### Fase 4 — Admin y Producción

- [ ] Panel admin (carpeta UI en raíz, p. ej. `platform-admin-web/`)
- [ ] `infra/kubernetes/` — manifests
- [ ] `infra/observability/` — Prometheus + Grafana
- [ ] Alta disponibilidad

---

## 16. Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Mensajería | WhatsApp Cloud API |
| Webhook | Node.js o FastAPI |
| IA Core | Python + FastAPI |
| RAG | Python + FastAPI + Qdrant |
| Odoo | Python MCP Server + Odoo JSON-RPC |
| UI dev (simulador) | Streamlit |
| UI admin (futuro) | React/Next.js + FastAPI |
| Cola / Cache | Redis |
| Base relacional | PostgreSQL |
| Base vectorial | Qdrant |
| Protocolo agentes | MCP |
| LLM | OpenAI / Ollama / Claude |
| Contenedores | Docker Compose |
| Orquestación | Kubernetes |
| Observabilidad | Prometheus + Grafana |

---

## 17. Resultado Final

La plataforma implementa una arquitectura de agentes conversacionales moderna, organizada en microservicios independientes:

- **`services/`** — entrada WhatsApp y cerebro IA.
- **`RAG/`** — conocimiento corporativo desacoplado.
- **`Odoo/`** — ERP como herramientas MCP (stock + CRM).
- **`Streamlit/`** — simulador de chat para desarrollo.
- **`infra/`** — despliegue local y producción.
- **`shared/contracts/`** — contratos entre servicios.

Esto permite evolucionar desde un entorno local de desarrollo hasta una plataforma empresarial escalable, añadiendo capacidades de RAG, agentes y herramientas externas sin acoplar los dominios entre sí.
