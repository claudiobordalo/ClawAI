from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from clawai.orchestrator.orchestrator import orchestrator


router = APIRouter()


DEFAULT_PROJECT = Path(r"D:\ClawAI")


class ImplementRequest(BaseModel):

    objective: str

    apply: bool = False

    project: str | None = None


@router.post("/implement")
def implement(
    request: ImplementRequest,
):

    project = (
        Path(request.project)
        if request.project
        else DEFAULT_PROJECT
    )

    result = orchestrator.execute(

        project=project,

        objective=request.objective,

        apply=request.apply,

    )

    return {

        "planning": result.planning,

        "research": result.research,

        "implementation": result.implementation,

        "review": result.review,

        "tests": result.tests,

        "preview": result.preview,

        "modified_files": result.modified_files,

        "project": str(project),

    }
