"""
FastAPI application factory for ClawAI backend.

This module creates and configures the FastAPI application with all
API routers from the clawai.api package.
"""

from __future__ import annotations

from fastapi import FastAPI

from clawai.api.tools_api import router as tools_router
from clawai.api.bridge_api import router as bridge_router
from clawai.api.chat_api import router as chat_router
from clawai.api.autonomy_api import router as autonomy_router
from clawai.api.intelligence_api import router as intelligence_router
from clawai.api.implement_api import router as implement_router
from clawai.api.workspaces_api import router as workspaces_router
from clawai.api.evolution_api import router as evolution_router

# Import to trigger autostart if enabled
import clawai.api  # noqa: F401


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ClawAI Backend",
        version="0.1.0",
        description="ClawAI autonomous coding agent backend server",
    )

    # Include all API routers
    app.include_router(tools_router, prefix="/api")
    app.include_router(bridge_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(autonomy_router, prefix="/api")
    app.include_router(intelligence_router, prefix="/api")
    app.include_router(implement_router, prefix="/api")
    app.include_router(workspaces_router, prefix="/api")
    app.include_router(evolution_router, prefix="/api")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}

    return app
