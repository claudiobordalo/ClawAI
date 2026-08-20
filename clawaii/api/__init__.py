from __future__ import annotations

import os

from . import tools_api
from .evolution_api import router as evolution_router
from clawai.evolution import evolution_engine

if not getattr(tools_api.router, "_clawai_evolution_registered", False):
    tools_api.router.include_router(evolution_router)
    setattr(tools_api.router, "_clawai_evolution_registered", True)

if os.getenv("CLAWAI_EVOLUTION_AUTOSTART", "1").strip().lower() in {"1", "true", "yes", "on"}:
    try:
        evolution_engine.start()
    except Exception:
        pass
