"""Conector CRM Odoo para NeoBotSeller."""

from __future__ import annotations

from typing import Any

from connectors.odoo_client import OdooClient

LEAD_FIELDS = [
    "id",
    "name",
    "contact_name",
    "email_from",
    "phone",
    "type",
    "stage_id",
    "expected_revenue",
    "probability",
    "description",
    "user_id",
    "create_date",
]

PARTNER_FIELDS = [
    "id",
    "name",
    "email",
    "phone",
    "mobile",
    "user_id",
    "customer_rank",
    "company_type",
    "comment",
]


class CrmConnector:
    def __init__(self, client: OdooClient) -> None:
        self.client = client

    def search_lead(
        self,
        *,
        query: str | None = None,
        lead_type: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        domain: list[Any] = []
        if query:
            domain.extend(
                [
                    "|",
                    "|",
                    ("name", "ilike", query),
                    ("contact_name", "ilike", query),
                    ("email_from", "ilike", query),
                ]
            )
        if lead_type in ("lead", "opportunity"):
            domain.append(("type", "=", lead_type))

        leads = self.client.search_read(
            "crm.lead",
            domain,
            LEAD_FIELDS,
            limit=limit,
            order="create_date desc",
        )
        return {"count": len(leads), "leads": leads}

    def get_lead(self, lead_id: int) -> dict[str, Any]:
        records = self.client.search_read(
            "crm.lead",
            [("id", "=", lead_id)],
            LEAD_FIELDS,
            limit=1,
        )
        if not records:
            return {"found": False, "message": f"Lead/oportunidad {lead_id} no encontrado"}
        return {"found": True, "lead": records[0]}

    def create_lead(
        self,
        *,
        name: str,
        contact_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        description: str | None = None,
        expected_revenue: float | None = None,
        lead_type: str = "lead",
    ) -> dict[str, Any]:
        values: dict[str, Any] = {
            "name": name,
            "type": lead_type if lead_type in ("lead", "opportunity") else "lead",
        }
        if contact_name:
            values["contact_name"] = contact_name
        if email:
            values["email_from"] = email
        if phone:
            values["phone"] = phone
        if description:
            values["description"] = description
        if expected_revenue is not None:
            values["expected_revenue"] = expected_revenue

        lead_id = self.client.create("crm.lead", values)
        return self.get_lead(lead_id)

    def update_stage(self, lead_id: int, stage_name: str) -> dict[str, Any]:
        stages = self.client.search_read(
            "crm.stage",
            [("name", "ilike", stage_name.strip())],
            ["id", "name"],
            limit=1,
        )
        if not stages:
            return {
                "success": False,
                "message": f"Etapa '{stage_name}' no encontrada",
            }

        stage = stages[0]
        self.client.write("crm.lead", [lead_id], {"stage_id": stage["id"]})
        result = self.get_lead(lead_id)
        result["success"] = True
        result["stage"] = stage
        return result

    def list_stages(self) -> dict[str, Any]:
        stages = self.client.search_read(
            "crm.stage",
            [],
            ["id", "name", "sequence"],
            limit=50,
            order="sequence asc",
        )
        return {"count": len(stages), "stages": stages}

    def list_advisors(self, *, query: str | None = None, limit: int = 20) -> dict[str, Any]:
        """Lista usuarios internos (asesores / comerciales)."""
        domain: list[Any] = [("share", "=", False), ("active", "=", True)]
        if query:
            domain.extend(
                [
                    "|",
                    ("name", "ilike", query),
                    ("login", "ilike", query),
                ]
            )
        users = self.client.search_read(
            "res.users",
            domain,
            ["id", "name", "login", "email"],
            limit=limit,
            order="name asc",
        )
        return {"count": len(users), "advisors": users}

    def _resolve_advisor_id(
        self,
        *,
        advisor_id: int | None = None,
        advisor_login: str | None = None,
        advisor_name: str | None = None,
    ) -> int | None:
        if advisor_id:
            return advisor_id
        if advisor_login:
            users = self.client.search_read(
                "res.users",
                [("login", "=ilike", advisor_login.strip())],
                ["id"],
                limit=1,
            )
            return users[0]["id"] if users else None
        if advisor_name:
            users = self.client.search_read(
                "res.users",
                [("name", "ilike", advisor_name.strip()), ("share", "=", False)],
                ["id"],
                limit=1,
            )
            return users[0]["id"] if users else None
        return None

    def create_customer(
        self,
        *,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        is_company: bool = False,
        comment: str | None = None,
        advisor_id: int | None = None,
        advisor_login: str | None = None,
        advisor_name: str | None = None,
    ) -> dict[str, Any]:
        """Crea cliente (res.partner) y opcionalmente asigna asesor (user_id)."""
        user_id = self._resolve_advisor_id(
            advisor_id=advisor_id,
            advisor_login=advisor_login,
            advisor_name=advisor_name,
        )

        values: dict[str, Any] = {
            "name": name.strip(),
            "company_type": "company" if is_company else "person",
            "customer_rank": 1,
        }
        if email:
            values["email"] = email.strip()
        if phone:
            values["phone"] = phone.strip()
        if comment:
            values["comment"] = comment
        if user_id:
            values["user_id"] = user_id

        partner_id = self.client.create("res.partner", values)
        return self.get_customer(partner_id)

    def get_customer(self, partner_id: int) -> dict[str, Any]:
        records = self.client.search_read(
            "res.partner",
            [("id", "=", partner_id)],
            PARTNER_FIELDS,
            limit=1,
        )
        if not records:
            return {"found": False, "message": f"Cliente {partner_id} no encontrado"}
        return {"found": True, "customer": records[0]}

    def assign_advisor(
        self,
        *,
        partner_id: int,
        advisor_id: int | None = None,
        advisor_login: str | None = None,
        advisor_name: str | None = None,
    ) -> dict[str, Any]:
        """Asigna un asesor comercial (user_id) a un cliente existente."""
        user_id = self._resolve_advisor_id(
            advisor_id=advisor_id,
            advisor_login=advisor_login,
            advisor_name=advisor_name,
        )
        if not user_id:
            return {
                "success": False,
                "message": "No se encontró el asesor indicado",
            }

        self.client.write("res.partner", [partner_id], {"user_id": user_id})
        result = self.get_customer(partner_id)
        result["success"] = True
        result["assigned_advisor_id"] = user_id
        return result

    def search_customer(
        self,
        *,
        query: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        domain: list[Any] = [("customer_rank", ">", 0)]
        if query:
            domain.extend(
                [
                    "|",
                    "|",
                    ("name", "ilike", query),
                    ("email", "ilike", query),
                    ("phone", "ilike", query),
                ]
            )
        customers = self.client.search_read(
            "res.partner",
            domain,
            PARTNER_FIELDS,
            limit=limit,
            order="name asc",
        )
        return {"count": len(customers), "customers": customers}

    def archive_lead(
        self,
        *,
        lead_id: int | None = None,
        query: str | None = None,
    ) -> dict[str, Any]:
        """Da de baja un lead/oportunidad (active=False). No borra el registro."""
        if lead_id:
            records = self.client.search_read(
                "crm.lead",
                [("id", "=", lead_id)],
                LEAD_FIELDS + ["active"],
                limit=1,
            )
        elif query:
            search = self.search_lead(query=query, limit=1)
            records = search.get("leads", [])
        else:
            raise ValueError("Indica lead_id o query para dar de baja el lead")

        if not records:
            return {
                "success": False,
                "message": "Lead/oportunidad no encontrado para dar de baja",
            }

        lead = records[0]
        if not lead.get("active", True):
            return {
                "success": True,
                "already_archived": True,
                "message": f"El lead '{lead.get('name')}' ya estaba dado de baja",
                "lead": lead,
            }

        self.client.write("crm.lead", [lead["id"]], {"active": False})
        result = self.get_lead(lead["id"])
        result["success"] = True
        result["message"] = f"Lead '{lead.get('name')}' dado de baja"
        return result
