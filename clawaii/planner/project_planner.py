from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clawai.ai.router import AIRouter
from clawai.indexing.project_indexer import project_indexer


@dataclass
class RelevantFile:

    path: str
    reason: str


class ProjectPlanner:

    def __init__(self) -> None:

        self.router = AIRouter()

    def select_files(
        self,
        project: str | Path,
        objective: str,
    ) -> str:

        index = project_indexer.build(project)

        listing = "\n".join(

            f"{f.path} | {f.language} | {f.lines} linhas"

            for f in index

        )

        prompt = f"""
Você é o arquiteto do ClawAI.

Seu trabalho NÃO é escrever código.

Seu trabalho é escolher SOMENTE os arquivos
necessários para implementar o objetivo.

Para cada arquivo explique em UMA linha
por que ele será modificado.

Projeto:

{listing}

Objetivo:

{objective}

Formato:

src/App.tsx
Motivo: ...

src/Explorer.tsx
Motivo: ...

Nunca invente arquivos que não existem,
exceto quando realmente for necessário criar
um novo arquivo.
"""

        return self.router.ask(prompt)


project_planner = ProjectPlanner()
