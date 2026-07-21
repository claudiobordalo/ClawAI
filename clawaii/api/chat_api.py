from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

from clawai.chat.chat_service import chat


router = APIRouter()


class ChatRequest(BaseModel):

    prompt: str


@router.post("/chat")
def chat_text(
    request: ChatRequest,
):

    answer = chat.ask(
        prompt=request.prompt,
    )

    return {
        "answer": answer
    }


@router.post("/chat/image")
async def chat_image(

    prompt: str = Form(...),
    image: UploadFile = File(...),

):

    temp = Path(".clawai/temp")

    temp.mkdir(
        parents=True,
        exist_ok=True,
    )

    file = temp / image.filename

    file.write_bytes(
        await image.read()
    )

    answer = chat.ask(
        prompt=prompt,
        image=str(file),
    )

    return {
        "answer": answer
    }
