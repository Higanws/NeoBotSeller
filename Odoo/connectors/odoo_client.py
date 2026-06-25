"""Cliente XML-RPC para Odoo 17."""

from __future__ import annotations

import xmlrpc.client
from dataclasses import dataclass
from typing import Any


@dataclass
class OdooConfig:
    url: str
    db: str
    login: str
    password: str


class OdooClient:
    def __init__(self, config: OdooConfig) -> None:
        self.config = config
        self._uid: int | None = None
        self._common = xmlrpc.client.ServerProxy(f"{config.url.rstrip('/')}/xmlrpc/2/common")
        self._models = xmlrpc.client.ServerProxy(f"{config.url.rstrip('/')}/xmlrpc/2/object")

    @property
    def uid(self) -> int:
        if self._uid is None:
            uid = self._common.authenticate(
                self.config.db,
                self.config.login,
                self.config.password,
                {},
            )
            if not uid:
                raise ConnectionError(
                    f"No se pudo autenticar en Odoo ({self.config.url}, db={self.config.db})"
                )
            self._uid = uid
        return self._uid

    def execute(
        self,
        model: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        return self._models.execute_kw(
            self.config.db,
            self.uid,
            self.config.password,
            model,
            method,
            args or [],
            kwargs or {},
        )

    def search_read(
        self,
        model: str,
        domain: list[Any],
        fields: list[str],
        *,
        limit: int = 20,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {"fields": fields, "limit": limit}
        if order:
            kwargs["order"] = order
        return self.execute(model, "search_read", [domain], kwargs)

    def create(self, model: str, values: dict[str, Any]) -> int:
        return self.execute(model, "create", [values])

    def write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        return self.execute(model, "write", [ids, values])
