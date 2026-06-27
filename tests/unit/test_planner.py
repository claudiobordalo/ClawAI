from __future__ import annotations

import pytest

from clawai.planning.planner import ExecutionPlan, PlanStep, Planner


def test_create_plan_success() -> None:
    planner = Planner()
    plan = planner.create_plan("Implementar o fluxo de planejamento")

    assert isinstance(plan, ExecutionPlan)
    assert plan.objective == "Implementar o fluxo de planejamento"
    assert len(plan.steps) == 1
    assert plan.steps[0].id == "step-1"
    assert plan.steps[0].description == "Implementar o fluxo de planejamento"
    assert plan.steps[0].status == "pending"


def test_create_plan_with_empty_objective_raises() -> None:
    planner = Planner()

    with pytest.raises(ValueError, match="objective"):
        planner.create_plan("")

    with pytest.raises(ValueError, match="objective"):
        planner.create_plan("   ")


def test_next_step_returns_pending_step() -> None:
    planner = Planner()
    plan = planner.create_plan("Teste")

    next_step = planner.next_step(plan)

    assert next_step is not None
    assert next_step.status == "pending"
    assert next_step.id == "step-1"


def test_complete_step_returns_new_plan() -> None:
    planner = Planner()
    plan = planner.create_plan("Executar tarefa")

    new_plan = planner.complete_step(plan, "step-1")

    assert new_plan is not plan
    assert new_plan.steps[0].status == "completed"
    assert plan.steps[0].status == "pending"


def test_fail_step_returns_new_plan() -> None:
    planner = Planner()
    plan = planner.create_plan("Executar tarefa")

    failed_plan = planner.fail_step(plan, "step-1")

    assert failed_plan is not plan
    assert failed_plan.steps[0].status == "failed"
    assert plan.steps[0].status == "pending"


def test_plan_fully_completed_next_step_none() -> None:
    planner = Planner()
    plan = planner.create_plan("Executar tarefa")
    completed_plan = planner.complete_step(plan, "step-1")

    assert planner.next_step(completed_plan) is None


def test_planstep_immutable() -> None:
    step = PlanStep(id="step-1", description="Teste")

    with pytest.raises(Exception):
        step.status = "completed"  # type: ignore[assignment]


def test_executionplan_immutable() -> None:
    plan = ExecutionPlan(objective="Teste", steps=(PlanStep(id="step-1", description="Teste"),))

    with pytest.raises(Exception):
        plan.objective = "Outra coisa"  # type: ignore[assignment]


def test_stable_operations_over_plan() -> None:
    planner = Planner()
    plan = planner.create_plan("Executar tarefa")
    plan_after_complete = planner.complete_step(plan, "step-1")
    plan_after_fail = planner.fail_step(plan, "step-1")

    assert plan.steps[0].status == "pending"
    assert plan_after_complete.steps[0].status == "completed"
    assert plan_after_fail.steps[0].status == "failed"
    assert plan.objective == plan_after_complete.objective == plan_after_fail.objective
