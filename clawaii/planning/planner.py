from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(frozen=True)
class PlanStep:
    id: str
    description: str
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionPlan:
    objective: str
    steps: tuple[PlanStep, ...] = ()


class Planner:
    """Responsável por criar e atualizar planos de execução imutáveis."""

    VALID_STATUSES = {"pending", "running", "completed", "failed"}

    def create_plan(self, objective: str, steps: Sequence[str] | None = None) -> ExecutionPlan:
        if not objective or not objective.strip():
            raise ValueError("Planner: 'objective' não pode ser vazio.")

        # Comportamento legado: um único passo derivado do objective
        if steps is None:
            first_step = PlanStep(
                id="step-1",
                description=objective.strip(),
                status="pending",
                metadata={},
            )
            return ExecutionPlan(objective=objective.strip(), steps=(first_step,))

        # Validações explícitas para steps
        if isinstance(steps, str):
            raise ValueError("Planner: 'steps' deve ser uma sequência de strings, não uma string única.")
        if not isinstance(steps, (list, tuple)):
            raise ValueError("Planner: 'steps' deve ser uma lista/tupla de strings.")
        if len(steps) == 0:
            raise ValueError("Planner: 'steps' não pode ser vazio quando fornecido.")

        steps_list: list[PlanStep] = []
        for idx, description in enumerate(steps):
            if not isinstance(description, str):
                raise ValueError(f"Planner: passo #{idx+1} contém descrição de tipo inválido.")
            description = description.strip()
            if not description:
                raise ValueError(f"Planner: passo #{idx+1} contém descrição inválida (vazia ou apenas espaços).")

            step_id = f"step-{idx+1}"
            steps_list.append(
                PlanStep(
                    id=step_id,
                    description=description,
                    status="pending",
                    metadata={},
                )
            )

        return ExecutionPlan(objective=objective.strip(), steps=tuple(steps_list))

    def next_step(self, plan: ExecutionPlan) -> PlanStep | None:
        for step in plan.steps:
            if step.status == "pending":
                return step
        return None

    def complete_step(self, plan: ExecutionPlan, step_id: str) -> ExecutionPlan:
        return self._update_step_status(plan=plan, step_id=step_id, status="completed")

    def fail_step(self, plan: ExecutionPlan, step_id: str) -> ExecutionPlan:
        return self._update_step_status(plan=plan, step_id=step_id, status="failed")

    def _update_step_status(
        self,
        plan: ExecutionPlan,
        step_id: str,
        status: str,
    ) -> ExecutionPlan:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Planner: status inválido '{status}'.")

        found = False
        updated_steps: list[PlanStep] = []

        for step in plan.steps:
            if step.id == step_id:
                found = True
                updated_steps.append(
                    PlanStep(
                        id=step.id,
                        description=step.description,
                        status=status,
                        metadata=step.metadata,
                    )
                )
            else:
                updated_steps.append(step)

        if not found:
            raise ValueError(f"Planner: passo com id '{step_id}' não encontrado.")

        return ExecutionPlan(objective=plan.objective, steps=tuple(updated_steps))


