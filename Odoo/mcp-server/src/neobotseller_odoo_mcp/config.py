from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    odoo_url: str
    odoo_db: str
    odoo_login: str
    odoo_password: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            odoo_url=os.getenv("ODOO_URL", "http://localhost:8069"),
            odoo_db=os.getenv("ODOO_DB_NAME", os.getenv("ODOO_DB", "neobotseller")),
            odoo_login=os.getenv("ODOO_LOGIN", os.getenv("ODOO_USER", "admin")),
            odoo_password=os.getenv(
                "ODOO_USER_PASSWORD", os.getenv("ODOO_PASSWORD", "admin")
            ),
        )
