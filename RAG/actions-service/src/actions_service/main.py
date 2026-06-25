"""Actions Service — orquestación MCP (Odoo + RAG)."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from actions_service.config import get_settings
from actions_service.orchestrator import ActionsOrchestrator

logger = logging.getLogger(__name__)

app = FastAPI(
    title="NeoBotSeller Actions Service",
    description="Hub MCP: Odoo stock/CRM + RAG documentación",
    version="0.1.0",
)


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    name: str
    result: Any


@lru_cache
def get_orchestrator() -> ActionsOrchestrator:
    return ActionsOrchestrator(get_settings())


@app.get("/health")
async def health() -> dict[str, Any]:
    orch = get_orchestrator()
    return {"status": "ok", "service": "actions-service", **orch.backends_info()}


@app.get("/v1/tools")
async def list_tools() -> dict[str, Any]:
    tools = get_orchestrator().list_tools()
    return {"count": len(tools), "tools": tools}


@app.post("/v1/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    try:
        result = get_orchestrator().call_tool(request.name, request.arguments)
        return ToolCallResponse(name=request.name, result=result)
    except Exception as exc:
        logger.exception("tool call failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
