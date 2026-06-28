from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from clawai.autopilot import auto_implement
from clawai.chat.chat_service import chat

ROOT = Path(__file__).resolve().parent

IGNORED_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
}


def _resolve_path(path: str) -> Path:
    target = (ROOT / path).resolve()

    if target != ROOT and ROOT not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid path")

    return target


def _payload(result: object) -> dict[str, object]:
    if isinstance(result, str):
        return {"answer": result}

    if is_dataclass(result):
        return asdict(result)

    if isinstance(result, dict):
        return result

    return {"answer": str(result)}


app = FastAPI(title="ClawAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str


class AutoImplementRequest(BaseModel):
    objective: str
    test_command: str = "uv run python -m pytest -q"
    max_iterations: int = Field(default=3, ge=1, le=5)
    max_files: int = Field(default=15, ge=1, le=20)


class AutoImplementStatusRequest(BaseModel):
    objective: str | None = None
    test_command: str = "uv run python -m pytest -q"
    max_iterations: int = Field(default=3, ge=1, le=5)
    max_files: int = Field(default=15, ge=1, le=20)


class AutoImplementStatusRequest(BaseModel):
    objective: str | None = None
    test_command: str = "uv run python -m pytest -q"
    max_iterations: int = Field(default=3, ge=1, le=5)
    max_files: int = Field(default=15, ge=1, le=20)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "vision": "qwen2.5vl:7b",
        "coder": "qwen3:8b",
        "reasoning": "deepseek-r1:8b",
    }


@app.post("/api/chat")
def chat_text(
    request: ChatRequest,
):
    return _payload(
        chat.ask(
            prompt=request.prompt,
        )
    )


@app.post("/api/auto/implement")
def auto_implement_route(
    request: AutoImplementRequest,
):
    try:
        result = auto_implement.implement(
            objective=request.objective,
            test_command=request.test_command,
            max_iterations=request.max_iterations,
            max_files=request.max_files,
        )
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/auto/implement/start")
def auto_implement_start(
    request: AutoImplementRequest,
):
    try:
        session = auto_implement.start(
            objective=request.objective,
            test_command=request.test_command,
            max_iterations=request.max_iterations,
            max_files=request.max_files,
        )
        return asdict(session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/auto/implement/status/{run_id}")
def auto_implement_status(
    run_id: str,
):
    try:
        return asdict(auto_implement.get_status(run_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.get("/api/auto/implement/events/{run_id}")
def auto_implement_events(
    run_id: str,
    after: int = 0,
):
    try:
        return [asdict(event) for event in auto_implement.list_events(run_id, after=after)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/auto/implement/stop/{run_id}")
def auto_implement_stop(
    run_id: str,
):
    try:
        return asdict(auto_implement.stop(run_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/chat/image")
async def chat_image(
    prompt: str = Form(...),
    image: UploadFile = File(...),
):
    temp = ROOT / ".clawai" / "temp"

    temp.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = Path(image.filename or "image.bin").name
    target = temp / filename
    target.write_bytes(
        await image.read()
    )

    return _payload(
        chat.ask(
            prompt=prompt,
            file=str(target),
        )
    )


@app.post("/api/chat/file")
async def chat_file(
    prompt: str = Form(...),
    file: UploadFile = File(...),
):
    temp = ROOT / ".clawai" / "temp"

    temp.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = Path(file.filename or "arquivo").name
    target = temp / filename
    target.write_bytes(
        await file.read()
    )

    suffix = target.suffix.lower()

    if suffix in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
    }:
        return _payload(
            chat.ask(
                prompt=prompt,
                file=str(target),
            )
        )

    raise HTTPException(
        status_code=415,
        detail=f"Tipo de arquivo ainda não suportado: {suffix}",
    )


@app.get("/api/tree")
def tree(path: str = ""):
    directory = ROOT if not path else _resolve_path(path)

    if not directory.exists():
        raise HTTPException(status_code=404, detail="Folder not found")

    if not directory.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a folder")

    items = []

    for child in sorted(
        directory.iterdir(),
        key=lambda p: (not p.is_dir(), p.name.lower()),
    ):
        if child.name in IGNORED_NAMES:
            continue

        items.append(
            {
                "name": child.name,
                "path": str(child.relative_to(ROOT)).replace("\\", "/"),
                "directory": child.is_dir(),
                "children": [],
            }
        )

    return items


@app.get("/api/file")
def file(path: str):
    target = _resolve_path(path)

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return target.read_text(encoding="utf-8", errors="ignore")


@app.post("/api/file")
def save_file(data: dict):
    target = _resolve_path(str(data["path"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(data["content"]), encoding="utf-8")
    return {"success": True}