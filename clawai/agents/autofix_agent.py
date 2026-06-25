from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from clawai.agents.patch_agent import patch_agent
from clawai.agents.patch_applier import patch_applier


@dataclass
class AutoFixResult:

    success: bool
    output: str
    iterations: int


class AutoFixAgent:

    def execute(
        self,
        project: str | Path,
        command: list[str],
        objective: str,
        max_iterations: int = 5,
    ) -> AutoFixResult:

        project = Path(project)

        output = ""

        for iteration in range(max_iterations):

            process = subprocess.run(
                command,
                cwd=project,
                capture_output=True,
                text=True,
            )

            output = (
                process.stdout +
                "\n" +
                process.stderr
            )

            if process.returncode == 0:

                return AutoFixResult(
                    success=True,
                    output=output,
                    iterations=iteration,
                )

            patches = patch_agent.generate(
                project=project,
                objective=f"""
O projeto apresentou o seguinte erro:

{output}

Objetivo original:

{objective}

Corrija somente o necessário.
"""
            )

            patch_applier.apply(
                project,
                patches,
            )

        return AutoFixResult(
            success=False,
            output=output,
            iterations=max_iterations,
        )


autofix_agent = AutoFixAgent()
