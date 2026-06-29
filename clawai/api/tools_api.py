from __future__ import annotations

from fastapi import APIRouter, HTTPException

from clawai.api.autonomy_api import router as autonomy_router
from clawai.api.bridge_api import router as bridge_router
from clawai.api.intelligence_api import router as intelligence_router
from clawai.integrations.composio import composio_service  # noqa: F401
from clawai.tools.registry import tool_registry

router = APIRouter()
router.include_router(autonomy_router)
router.include_router(bridge_router)
router.include_router(intelligence_router)


@router.get("/tools")
def list_tools():
    return {
        "tools": tool_registry.names(),
    }


@router.get("/tools/connections")
def list_connections():
    try:
        composio = tool_registry.get("composio")
        response = composio.connections()
        connections = []

        for item in response:
            connections.append(
                {
                    "toolkit": item.get("toolkit") if isinstance(item, dict) else getattr(item, "toolkit", ""),
                    "status": item.get("status") if isinstance(item, dict) else getattr(item, "status", ""),
                    "user_id": item.get("user_id") if isinstance(item, dict) else getattr(item, "user_id", ""),
                }
            )

        return {
            "connections": connections,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
