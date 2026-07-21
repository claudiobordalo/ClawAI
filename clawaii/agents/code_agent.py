from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clawai.ai.router import AIRouter
from clawai.workspace.workspace import workspace


@dataclass
class CodePlan:

    objective: str
    project_context: str
    response: str


class CodeAgent:

    def __init__(self) -> None:

        self.router = AIRouter()

    def plan(
        self,
        project: str | Path,
        objective: str,
    ) -> CodePlan:

        context = workspace.build_context(
            project,
            max_chars=100000,
        )

        prompt = f"""
Você é o CodeAgent do ClawAI.

Analise cuidadosamente o projeto abaixo.

Sua tarefa NÃO é escrever código ainda.

Sua tarefa é criar um plano técnico.

Responda exatamente nesta estrutura:

## Resumo

## Arquivos que precisam ser alterados

## Novos arquivos

## Etapas

## Riscos

Projeto:

{context}

Objetivo:

{objective}
"""

        answer = self.router.ask(prompt)

        return CodePlan(
            objective=objective,
            project_context=context,
            response=answer,
        )


code_agent = CodeAgent()
