from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clawai.agents.patch_agent import patch_agent
from clawai.agents.patch_applier import patch_applier
from clawai.agents.team_leader import team_leader


@dataclass
class ExecutionResult:

    planning: str

    research: str

    implementation: str

    review: str

    tests: str

    preview: str

    modified_files: list[str]


class Orchestrator:

    def execute(
        self,
        project: str | Path,
        objective: str,
        apply: bool = False,
    ) -> ExecutionResult:

        team = team_leader.execute(
            objective=objective,
        )

        patches = patch_agent.generate(
            project=project,
            objective=f"""
Objetivo:

{objective}

Planejamento:

{team.planning}

Pesquisa:

{team.research}

Implementação:

{team.implementation}

Revisão:

{team.review}

Testes:

{team.tests}
""",
        )

        preview = patch_applier.preview(
            project,
            patches,
        )

        modified_files = []

        if apply:

            modified_files = patch_applier.apply(
                project,
                patches,
            )

        return ExecutionResult(

            planning=team.planning,

            research=team.research,

            implementation=team.implementation,

            review=team.review,

            tests=team.tests,

            preview=preview,

            modified_files=modified_files,

        )


orchestrator = Orchestrator()
