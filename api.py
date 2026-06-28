from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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


def _sse(event: str, payload: dict[str, object]) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    )


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
    return asdict(
        chat.ask(
            prompt=request.prompt,
        )
    )


@app.post("/api/chat/stream")
def chat_text_stream(
    request: ChatRequest,
):
    def event_stream():
        try:
            for item in chat.ask_stream(request.prompt):
                event = str(item.get("type", "message"))
                payload = {
                    key: value
                    for key, value in item.items()
                    if key != "type"
                }
                yield _sse(event, payload)
        except Exception as exc:
            yield _sse(
                "error",
                {
                    "message": str(exc),
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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
    target.write_bytes(await image.read())

    return asdict(
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
    target.write_bytes(await file.read())

    suffix = target.suffix.lower()

    if suffix in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
    }:
        return asdict(
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