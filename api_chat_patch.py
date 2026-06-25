from pathlib import Path
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from clawai.workspace.services.project_analyzer import ProjectAnalyzer
from clawai.application.application import Application

ROOT = Path(r"D:\ClawAI")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assistant = Application()


class ChatRequest(BaseModel):
    question: str


@app.post("/api/chat")
def chat(request: ChatRequest):

    answer = assistant.ask(
        workspace=str(ROOT),
        question=request.question
    )

    return {
        "answer": answer
    }
