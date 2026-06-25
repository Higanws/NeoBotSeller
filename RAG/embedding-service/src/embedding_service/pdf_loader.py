"""Extracción de texto desde PDF."""

from __future__ import annotations

import logging
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """Devuelve lista de (número_página, texto)."""
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((index, text))
    logger.info("PDF %s: %s páginas con texto", path.name, len(pages))
    return pages
