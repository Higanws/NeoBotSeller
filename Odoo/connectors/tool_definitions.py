"""Definiciones de herramientas Odoo (contrato MCP / OpenAI tools)."""

from __future__ import annotations

from typing import Any

ODOO_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "stock_get_product",
            "description": (
                "Consulta existencias y datos de un producto por SKU o nombre. "
                "Usar cuando pregunten por stock, precio o disponibilidad."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Código SKU"},
                    "name": {"type": "string", "description": "Nombre del producto"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_check_availability",
            "description": "Verifica stock suficiente para uno o varios productos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "sku": {"type": "string"},
                                "name": {"type": "string"},
                                "quantity": {"type": "number"},
                            },
                        },
                    }
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_list_inventory",
            "description": "Lista productos con cantidades disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "warehouse_name": {"type": "string"},
                    "low_stock_only": {"type": "boolean"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_create_product",
            "description": (
                "Crea un nuevo producto almacenable en Odoo. "
                "Usar cuando el usuario pida crear/registrar un producto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nombre del producto"},
                    "sku": {"type": "string", "description": "Código SKU / referencia"},
                    "list_price": {"type": "number", "description": "Precio de venta"},
                    "standard_price": {"type": "number", "description": "Coste"},
                    "initial_qty": {
                        "type": "number",
                        "description": "Cantidad inicial en inventario",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_archive_product",
            "description": (
                "Da de baja (archiva) un producto en Odoo. "
                "Usar cuando pidan eliminar, archivar o dar de baja un producto. "
                "No borra el registro, lo desactiva (active=False)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto en Odoo"},
                    "sku": {"type": "string", "description": "SKU / referencia"},
                    "name": {"type": "string", "description": "Nombre del producto"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_list_low_stock",
            "description": "Lista productos con existencias bajas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "number", "default": 10},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_search_lead",
            "description": "Busca leads u oportunidades por nombre, contacto o email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "lead_type": {"type": "string", "enum": ["lead", "opportunity"]},
                    "limit": {"type": "integer", "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_create_lead",
            "description": "Crea un lead u oportunidad en el CRM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "contact_name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "description": {"type": "string"},
                    "expected_revenue": {"type": "number"},
                    "lead_type": {"type": "string", "enum": ["lead", "opportunity"]},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_get_lead",
            "description": "Obtiene detalle de lead/oportunidad por ID.",
            "parameters": {
                "type": "object",
                "properties": {"lead_id": {"type": "integer"}},
                "required": ["lead_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_update_stage",
            "description": "Mueve un lead a otra etapa del pipeline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "stage_name": {"type": "string"},
                },
                "required": ["lead_id", "stage_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_list_stages",
            "description": "Lista etapas del pipeline CRM.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_list_advisors",
            "description": "Lista asesores/comerciales disponibles para asignar clientes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Filtrar por nombre o login"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_create_customer",
            "description": (
                "Crea un cliente en Odoo (res.partner) y opcionalmente lo asigna a un asesor. "
                "Usar cuando pidan registrar/crear un cliente nuevo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nombre del cliente"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "is_company": {"type": "boolean", "default": False},
                    "comment": {"type": "string"},
                    "advisor_id": {"type": "integer", "description": "ID del asesor (res.users)"},
                    "advisor_login": {"type": "string", "description": "Login del asesor, ej. admin"},
                    "advisor_name": {"type": "string", "description": "Nombre del asesor"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_assign_advisor",
            "description": "Asigna un asesor comercial a un cliente existente por partner_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "partner_id": {"type": "integer", "description": "ID del cliente en Odoo"},
                    "advisor_id": {"type": "integer"},
                    "advisor_login": {"type": "string"},
                    "advisor_name": {"type": "string"},
                },
                "required": ["partner_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_archive_lead",
            "description": (
                "Da de baja (archiva) un lead u oportunidad en el CRM. "
                "Usar cuando pidan eliminar, archivar o dar de baja un lead. "
                "No borra el registro, lo desactiva (active=False)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer", "description": "ID del lead en Odoo"},
                    "query": {
                        "type": "string",
                        "description": "Nombre, contacto o email para localizar el lead",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crm_search_customer",
            "description": "Busca clientes existentes por nombre, email o teléfono.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
            },
        },
    },
]
