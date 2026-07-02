from __future__ import annotations

import json
from typing import Any


class Synthesizer:
    def __init__(self, *, router: Any) -> None:
        self.router = router

    def synthesize(self, *, objective: str, history: list[dict[str, Any]]) -> str:
        system_prompt = "Você é o sintetizador do runtime. Resuma a resposta final em português com base no histórico estrutural."
        payload = (
            f"Objetivo: {objective}\n\n"
            f"Histórico: {json.dumps(history, ensure_ascii=False)}"
        )
        return self.router.ask(prompt=payload, role="default", system_prompt=system_prompt)
