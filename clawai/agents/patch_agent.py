from __future__ import annotations

import json

from clawai.ai.router import AIRouter
from clawai.context.context_builder import context_builder
from clawai.workspace.file_reader import FileReader
from clawai.workspace.ignore import IgnoreEngine
from clawai.workspace.scanner import Scanner
from clawai.workspace.workspace import Workspace


class PatchAgent:


    def __init__(self) -> None:

        self.router = AIRouter()

    def generate(
        self,
        project: str,
        objective: str,
    ) -> list[dict]:

        ws = Workspace()
        ws.open_project(project)
        tree = ws.get_tree()

        ignore = IgnoreEngine(project)
        ignore.load()

        scanner = Scanner(project, ignore_engine=ignore)
        file_reader = FileReader()

        context_result = context_builder.build(
            objective=objective,
            project_tree=tree,
            scanner=scanner,
            file_reader=file_reader,
            max_files=25,
            max_chars=120000,
        )

        context = context_result.context


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
