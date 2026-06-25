from __future__ import annotations

import json

from clawai.ai.router import AIRouter
from clawai.workspace.workspace import workspace


class PatchAgent:

    def __init__(self) -> None:

        self.router = AIRouter()

    def generate(
        self,
        project: str,
        objective: str,
    ) -> list[dict]:

        context = workspace.build_context(
            project,
            max_chars=120000,
        )

        prompt = f"""
Você é o PatchAgent do ClawAI.

Nunca reescreva arquivos completos.

Sempre gere operações.

Formato obrigatório:

[
  {{
    "path":"src/App.tsx",
    "operations":[
      {{
        "type":"replace",
        "search":"texto antigo",
        "replace":"texto novo"
      }}
    ]
  }}
]

Tipos permitidos:

replace
insert_before
insert_after
delete

Projeto:

{context}

Objetivo:

{objective}

Responda SOMENTE com JSON.
"""

        answer = self.router.ask(prompt)

        begin = answer.find("[")

        end = answer.rfind("]")

        if begin == -1 or end == -1:
            raise Exception("JSON inválido.")

        return json.loads(
            answer[begin:end + 1]
        )


patch_agent = PatchAgent()
