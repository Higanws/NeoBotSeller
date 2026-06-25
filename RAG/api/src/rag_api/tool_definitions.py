"""Definiciones de herramientas RAG para el servicio de acciones."""

from __future__ import annotations

from typing import Any

RAG_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "rag_search_documents",
            "description": (
                "Busca en la documentación corporativa indexada (PDFs: catálogos, políticas, manuales). "
                "Invócala cuando el usuario pregunte por información documental que no está en Odoo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Pregunta o términos de búsqueda"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]
