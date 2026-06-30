from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from clawai.evolution import evolution_engine

router = APIRouter()


@router.get("/evolution/state")
def evolution_state():
    return asdict(evolution_engine.get_state())


@router.get("/evolution/backlog")
def evolution_backlog():
    return evolution_engine.backlog_overview()


@router.get("/evolution/history")
def evolution_history(limit: int = 20):
    return evolution_engine.list_history(limit=limit)


@router.post("/evolution/start")
def evolution_start():
    return asdict(evolution_engine.start())


@router.post("/evolution/stop")
def evolution_stop():
    return asdict(evolution_engine.stop())


@router.post("/evolution/run-once")
def evolution_run_once():
    try:
        return asdict(evolution_engine.run_once())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/evolution/rebuild")
def evolution_rebuild():
    try:
        backlog = evolution_engine.rebuild_backlog()
        return {
            "count": len(backlog),
            "items": [item.to_dict() for item in backlog],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
