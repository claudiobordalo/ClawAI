from __future__ import annotations

from fastapi import APIRouter, HTTPException

from clawai.tools.registry import tool_registry


router = APIRouter()


@router.get("/tools")
def list_tools():

    return {
        "tools": tool_registry.names(),
    }


@router.get("/tools/connections")
def list_connections():

    try:

        composio = tool_registry.get(
            "composio",
        )

        response = composio.connections()

        connections = []

        for item in response.items:

            connections.append(
                {
                    "toolkit": item.toolkit.slug,
                    "status": item.status,
                    "user_id": item.user_id,
                }
            )

        return {
            "connections": connections,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
