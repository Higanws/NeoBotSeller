"""Cliente HTTP hacia actions-service (hub MCP unificado)."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from ia_core.config import Settings

logger = logging.getLogger(__name__)


class ActionsHub:
    """Descubre y ejecuta herramientas MCP vía actions-service."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._base = settings.actions_service_url.rstrip("/")
        self._tools_cache: list[dict[str, Any]] | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.actions_service_url)

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        if self._tools_cache is not None:
            return self._tools_cache
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{self._base}/v1/tools")
            response.raise_for_status()
            self._tools_cache = response.json().get("tools", [])
        return self._tools_cache

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if not self.enabled:
            raise RuntimeError("ACTIONS_SERVICE_URL no configurada")
        payload = {"name": name, "arguments": arguments}
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{self._base}/v1/tools/call", json=payload)
            response.raise_for_status()
            data = response.json()
        return json.dumps(data.get("result"), ensure_ascii=False)
