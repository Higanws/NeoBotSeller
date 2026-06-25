# Documentos RAG

Coloca aquí los **PDF** que quieras indexar.

```bash
cp /ruta/a/catalogo.pdf RAG/documents/
```

Luego ejecuta la ingesta:

```bash
curl -X POST http://localhost:8094/v1/ingest
```

O arranca el embedding-service con `EMBEDDING_WATCH=true` para indexar automáticamente al detectar PDFs nuevos.
