from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from clawai.workspaces.state import workspace_state

router = APIRouter(prefix="/workspaces")


class WorkspaceOpenRequest(BaseModel):
    path: str
    name: str | None = None


class WorkspaceSelectRequest(BaseModel):
    workspace_id: str


class WorkspaceSaveRequest(BaseModel):
    path: str
    content: str
    workspace_id: str | None = None


@router.get("")
def list_workspaces():
    return workspace_state.summary()


@router.post("/open")
def open_workspace(request: WorkspaceOpenRequest):
    try:
        ws = workspace_state.open(request.path, request.name)
        return {"workspace": ws.__dict__, "summary": workspace_state.summary()}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"Workspace folder not found: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/select")
def select_workspace(request: WorkspaceSelectRequest):
    try:
        ws = workspace_state.select(request.workspace_id)
        return {"workspace": ws.__dict__, "summary": workspace_state.summary()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found") from exc


@router.post("/close/{workspace_id}")
def close_workspace(workspace_id: str):
    try:
        return {"workspaces": [ws.__dict__ for ws in workspace_state.close(workspace_id)], "summary": workspace_state.summary()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/current")
def current_workspace():
    return workspace_state.current().__dict__


@router.get("/tree")
def tree(path: str = "", workspace_id: str | None = None):
    try:
        return workspace_state.tree(path, workspace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Folder not found")
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/file")
def read_file(path: str, workspace_id: str | None = None):
    try:
        return workspace_state.read(path, workspace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/file")
def write_file(request: WorkspaceSaveRequest):
    try:
        return workspace_state.write(request.path, request.content, request.workspace_id)
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
