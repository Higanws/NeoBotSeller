# Embedding Service — PDF → Qdrant

Servicio propio de **ingesta y embeddings** para el RAG de NeoBotSeller.

## Qué hace

1. Lee PDFs de `RAG/documents/`
2. Extrae texto, divide en chunks
3. Genera embeddings (local con fastembed, sin API key)
4. Almacena vectores en **Qdrant**

## Requisitos

- Qdrant en marcha (`RAG/qdrant`)
- Python 3.10+

## Inicio

```bash
# 1. Qdrant
cd RAG/qdrant && docker compose up -d

# 2. Coloca PDFs
cp tu-catalogo.pdf ../documents/

# 3. Embedding service
cd ../embedding-service
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=src uvicorn embedding_service.main:app --reload --port 8094

# 4. Indexar
curl -X POST http://localhost:8094/v1/ingest
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado + stats Qdrant |
| GET | `/v1/documents` | PDFs en carpeta |
| POST | `/v1/ingest` | Indexar todos los PDF |
| POST | `/v1/ingest/{filename}` | Indexar un PDF |
| POST | `/v1/embed` | Embedding de un texto |
| POST | `/v1/search` | Búsqueda semántica directa |

## Variables

```env
DOCUMENTS_DIR=../documents
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=neobotseller
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_WATCH=false   # true = re-indexa al detectar PDFs nuevos
```

## OpenAI (opcional)

```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Consumidores

| Servicio | Uso |
|----------|-----|
| `RAG/api` | `EMBEDDING_SERVICE_URL` para retrieval en chat |
| `RAG/actions-service` | búsqueda vía `RAG/api` `/v1/search` |
