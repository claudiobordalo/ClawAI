from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from clawai.autopilot.autonomy_coordinator import autonomy

router = APIRouter()


class AutonomyObjectiveRequest(BaseModel):
    objective: str
    test_command: str = "uv run python -m pytest -q"
    max_iterations: int = Field(default=3, ge=1, le=5)
    max_files: int = Field(default=15, ge=1, le=20)


@router.post("/autonomy/queue")
def enqueue_autonomy(request: AutonomyObjectiveRequest):
    try:
        item = autonomy.enqueue(
            objective=request.objective,
            test_command=request.test_command,
            max_iterations=request.max_iterations,
            max_files=request.max_files,
        )
        return asdict(item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/autonomy/queue")
def list_autonomy_queue():
    return [asdict(item) for item in autonomy.list_queue()]


@router.get("/autonomy/plans")
def list_autonomy_plans():
    return [asdict(plan) for plan in autonomy.list_plans()]


@router.get("/autonomy/plans/{objective_id}")
def get_autonomy_plan(objective_id: str):
    plan = autonomy.get_plan(objective_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return asdict(plan)


@router.get("/autonomy/memory")
def list_autonomy_memory(objective: str = "", limit: int = 20):
    objective_filter = objective.strip() or None
    return [asdict(entry) for entry in autonomy.list_memory(objective_filter, limit=limit)]


@router.get("/autonomy/state")
def autonomy_state():
    return autonomy.get_state()
