"""Pipeline: PDF en carpeta → chunks → embeddings → Qdrant."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from embedding_service.chunker import split_text
from embedding_service.config import Settings
from embedding_service.embedder import Embedder
from embedding_service.pdf_loader import extract_pdf_pages
from embedding_service.qdrant_store import QdrantStore

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    files_processed: int = 0
    chunks_indexed: int = 0
    errors: list[str] = field(default_factory=list)


class IngestPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedder = Embedder(settings)
        self.store = QdrantStore(
            settings.qdrant_url,
            settings.qdrant_collection,
            self.embedder.vector_size,
        )
        self._indexed_mtimes: dict[str, float] = {}

    def list_pdfs(self) -> list[Path]:
        docs_dir = self.settings.documents_dir
        docs_dir.mkdir(parents=True, exist_ok=True)
        return sorted(docs_dir.glob("*.pdf"))

    def ingest_all(self, *, force: bool = False) -> IngestResult:
        result = IngestResult()
        for pdf_path in self.list_pdfs():
            try:
                chunks = self.ingest_file(pdf_path, force=force)
                result.files_processed += 1
                result.chunks_indexed += chunks
            except Exception as exc:
                logger.exception("Error indexando %s", pdf_path.name)
                result.errors.append(f"{pdf_path.name}: {exc}")
        return result

    def ingest_file(self, path: Path, *, force: bool = False) -> int:
        path = path.resolve()
        if path.suffix.lower() != ".pdf":
            raise ValueError("Solo se admiten archivos PDF")

        mtime = path.stat().st_mtime
        cache_key = str(path)
        if not force and self._indexed_mtimes.get(cache_key) == mtime:
            logger.debug("Omitiendo %s (sin cambios)", path.name)
            return 0

        pages = extract_pdf_pages(path)
        chunks: list[str] = []
        chunk_meta: list[dict] = []

        for page_num, page_text in pages:
            for chunk in split_text(
                page_text,
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
            ):
                chunks.append(chunk)
                chunk_meta.append({"page": page_num, "filename": path.name})

        if not chunks:
            logger.warning("PDF sin texto extraíble: %s", path.name)
            self._indexed_mtimes[cache_key] = mtime
            return 0

        vectors = self.embedder.embed_texts(chunks)
        indexed = 0
        batch_size = 32
        for start in range(0, len(chunks), batch_size):
            end = start + batch_size
            indexed += self.store.upsert_chunks(
                source=path.name,
                chunks=chunks[start:end],
                vectors=vectors[start:end],
                metadatas=chunk_meta[start:end],
            )

        self._indexed_mtimes[cache_key] = mtime
        logger.info("Indexado %s: %s chunks", path.name, indexed)
        return indexed

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        vector = self.embedder.embed_text(query)
        return self.store.search(vector, top_k=top_k)

    def stats(self) -> dict:
        return {
            "documents_dir": str(self.settings.documents_dir),
            "pdf_count": len(self.list_pdfs()),
            "embedding_provider": self.settings.embedding_provider,
            "embedding_model": self.settings.embedding_model,
            "vector_size": self.embedder.vector_size,
            **self.store.collection_stats(),
        }
