# Qdrant — Vector store RAG

Base de vectores para embeddings documentales de NeoBotSeller.

## Inicio

```bash
cd RAG/qdrant
docker compose up -d
```

## Acceso

| Recurso | URL |
|---------|-----|
| HTTP API | http://localhost:6333 |
| Dashboard | http://localhost:6333/dashboard |
| Colección | `neobotseller` (creada por embedding-service) |

## Variables

```env
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=neobotseller
```
