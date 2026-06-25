from __future__ import annotations

import json

from clawai.ai.router import AIRouter
from clawai.context.context_builder import context_builder
from clawai.dispatcher.agent_registry import AgentRegistry, PatchAgentAdapter
from clawai.dispatcher.dispatcher import Dispatcher
from clawai.mission.mission import Mission
from clawai.mission.mission_executor import MissionExecutor
from clawai.mission.mission_state import MissionStepStatus
from clawai.mission.mission_step import MissionStep
from clawai.workspace.file_reader import FileReader
from clawai.workspace.ignore import IgnoreEngine
from clawai.workspace.scanner import Scanner
from clawai.workspace.workspace import Workspace


class PatchAgent:
    def __init__(self) -> None:
        self.router = AIRouter()

    def _execute_patch(
        self,
        *,
        project: str,
        objective: str,
    ) -> list[dict]:
        # Execução direta da lógica de patch, evitando recursão circular
        # entre MissionExecutor/Dispatcher e PatchAgentAdapter.
        return self._generate_patch_ops(project=project, objective=objective)

    def _generate_patch_ops(
        self,
        *,
        project: str,
        objective: str,
    ) -> list[dict]:
        ws = Workspace()
        ws.open_project(project)
        _tree = ws.get_tree()  # reservado para possíveis heurísticas futuras

        ignore = IgnoreEngine(project)
        ignore.load()

        scanner = Scanner(project, ignore_engine=ignore)
        file_reader = FileReader()

        context_result = context_builder.build(
            objective=objective,
            project_tree=_tree,
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
""".strip()

        answer = self.router.ask(prompt)

        begin = answer.find("[")
        end = answer.rfind("]")
        if begin == -1 or end == -1:
            raise Exception("JSON inválido.")

        ops = json.loads(answer[begin : end + 1])
        return ops

    def generate(
        self,
        project: str,
        objective: str,
    ) -> list[dict]:
        return self._execute_patch(project=project, objective=objective)


patch_agent = PatchAgent()
