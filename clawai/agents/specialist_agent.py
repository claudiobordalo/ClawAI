from __future__ import annotations

from dataclasses import dataclass

from clawai.ai.router import AIRouter


@dataclass
class AgentResponse:

    agent: str

    response: str


class SpecialistAgent:

    def __init__(
        self,
        role: str,
    ) -> None:

        self.role = role

        self.router = AIRouter()

    def execute(
        self,
        task: str,
    ) -> AgentResponse:

        prompt = f"""
Você é um especialista.

Especialidade:

{self.role}

Responda somente sob a perspectiva da sua especialidade.

Tarefa:

{task}
"""

        return AgentResponse(

            agent=self.role,

            response=self.router.ask(prompt),

        )


planner_agent = SpecialistAgent("Software Architect")

coder_agent = SpecialistAgent("Senior Software Engineer")

reviewer_agent = SpecialistAgent("Code Reviewer")

tester_agent = SpecialistAgent("QA Engineer")

research_agent = SpecialistAgent("Research Engineer")
