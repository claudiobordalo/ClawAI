from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from clawai.chat.chat_service import chat

ROOT = Path(r"D:\ClawAI").resolve()

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

    return {
        "answer": chat.ask(
            prompt=request.prompt,
        )
    }


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

    return {
        "answer": chat.ask(
            prompt=prompt,
            image=str(target),
        )
    }


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

        return {
            "answer": chat.ask(
                prompt=prompt,
                image=str(target),
            )
        }

    raise HTTPException(
        status_code=415,
        detail=f"Tipo de arquivo ainda não suportado: {suffix}"
    )
