from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from clawai.api.tools_api import router as tools_router
from clawai.autopilot import auto_implement
from clawai.chat.chat_service import chat
from clawai.workspaces.state import workspace_state

ROOT = Path(__file__).resolve().parent
IGNORED_NAMES = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "node_modules"}


class ChatRequest(BaseModel):
    prompt: str


class AutoImplementRequest(BaseModel):
    objective: str
    test_command: str = "uv run python -m pytest -q"
    max_iterations: int = Field(default=3, ge=1, le=5)
    max_files: int = Field(default=15, ge=1, le=20)


class WorkspaceOpenRequest(BaseModel):
    path: str
    name: str | None = None


class WorkspaceSelectRequest(BaseModel):
    workspace_id: str


class SaveFileRequest(BaseModel):
    path: str
    content: str
    workspace_id: str | None = None


def _payload(result: object) -> dict[str, object]:
    if isinstance(result, str):
        return {"answer": result}
    if is_dataclass(result):
        return asdict(result)
    if isinstance(result, dict):
        return result
    return {"answer": str(result)}


def _read_verify_report() -> tuple[str | None, dict[str, object] | None]:
    report_path = ROOT / "verify_report.json"
    if not report_path.exists():
        return None, None
    report_text = report_path.read_text(encoding="utf-8", errors="ignore")
    try:
        parsed = json.loads(report_text)
    except Exception:
        parsed = None
    return report_text, parsed if isinstance(parsed, dict) else None


app = FastAPI(title="ClawAI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "vision": "qwen2.5vl:7b", "coder": "qwen3:8b", "reasoning": "deepseek-r1:8b"}


@app.get("/api/workspaces")
def list_workspaces():
    return workspace_state.summary()


@app.get("/api/workspaces/current")
def current_workspace():
    return asdict(workspace_state.current())


@app.post("/api/workspaces/open")
def open_workspace(request: WorkspaceOpenRequest):
    try:
        workspace = workspace_state.open(request.path, name=request.name)
        return {"workspace": asdict(workspace), "summary": workspace_state.summary()}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=f"Workspace folder not found: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/workspaces/select")
def select_workspace(request: WorkspaceSelectRequest):
    try:
        workspace = workspace_state.select(request.workspace_id)
        return {"workspace": asdict(workspace), "summary": workspace_state.summary()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found") from exc


@app.post("/api/workspaces/close/{workspace_id}")
def close_workspace(workspace_id: str):
    try:
        return {"workspaces": [asdict(item) for item in workspace_state.close(workspace_id)], "summary": workspace_state.summary()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/chat")
def chat_text(request: ChatRequest):
    return _payload(chat.ask(prompt=request.prompt))


@app.post("/api/auto/implement")
def auto_implement_route(request: AutoImplementRequest):
    try:
        result = auto_implement.implement(objective=request.objective, test_command=request.test_command, max_iterations=request.max_iterations, max_files=request.max_files)
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/auto/implement/start")
def auto_implement_start(request: AutoImplementRequest):
    try:
        session = auto_implement.start(objective=request.objective, test_command=request.test_command, max_iterations=request.max_iterations, max_files=request.max_files)
        return asdict(session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/auto/implement/status/{run_id}")
def auto_implement_status(run_id: str):
    try:
        session = auto_implement.get_status(run_id)
        payload = asdict(session)
        result = session.result
        payload["verify_success"] = result.verify_success if result else None
        payload["verify_return_code"] = result.verify_return_code if result else None
        payload["verify_summary"] = result.verify_summary if result else ""
        payload["verify_timestamp"] = result.verify_timestamp if result else ""
        payload["verify_report"] = result.verify_report if result else ""
        payload["verify_report_data"] = result.verify_report_data if result else {}
        payload["git_enabled"] = result.git_enabled if result else False
        payload["git_base_branch"] = result.git_base_branch if result else ""
        payload["git_branch"] = result.git_branch if result else ""
        payload["git_snapshot_commit"] = result.git_snapshot_commit if result else ""
        payload["git_commit"] = result.git_commit if result else ""
        payload["git_commit_success"] = result.git_commit_success if result else False
        payload["git_commit_message"] = result.git_commit_message if result else ""
        payload["git_rollback_performed"] = result.git_rollback_performed if result else False
        payload["git_rollback_reason"] = result.git_rollback_reason if result else ""
        payload["git_dirty_snapshot"] = result.git_dirty_snapshot if result else False
        return payload
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.get("/api/auto/implement/events/{run_id}")
def auto_implement_events(run_id: str, after: int = 0):
    try:
        return [asdict(event) for event in auto_implement.list_events(run_id, after=after)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/auto/implement/stop/{run_id}")
def auto_implement_stop(run_id: str):
    try:
        return asdict(auto_implement.stop(run_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/verify")
def verify_route():
    process = subprocess.run([sys.executable, "verify.py"], cwd=ROOT, capture_output=True, text=True)
    report_text, report_data = _read_verify_report()
    return {"success": process.returncode == 0, "return_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr, "report_text": report_text, "report": report_data if report_data is not None else report_text, "report_data": report_data}


@app.post("/api/chat/image")
async def chat_image(prompt: str = Form(...), image: UploadFile = File(...)):
    temp = ROOT / ".clawai" / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    target = temp / Path(image.filename or "image.bin").name
    target.write_bytes(await image.read())
    return _payload(chat.ask(prompt=prompt, file=str(target)))


@app.post("/api/chat/file")
async def chat_file(prompt: str = Form(...), file: UploadFile = File(...)):
    temp = ROOT / ".clawai" / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    target = temp / Path(file.filename or "arquivo").name
    target.write_bytes(await file.read())
    if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        return _payload(chat.ask(prompt=prompt, file=str(target)))
    raise HTTPException(status_code=415, detail=f"Tipo de arquivo ainda não suportado: {target.suffix.lower()}")


@app.get("/api/tree")
def tree(path: str = "", workspace_id: str | None = None):
    try:
        return workspace_state.tree(path=path, workspace_id=workspace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Folder not found")
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/file")
def file(path: str, workspace_id: str | None = None):
    try:
        return workspace_state.read(path=path, workspace_id=workspace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/file")
def save_file(data: SaveFileRequest):
    try:
        return workspace_state.write(path=data.path, content=data.content, workspace_id=data.workspace_id)
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


app.include_router(tools_router, prefix="/api")
