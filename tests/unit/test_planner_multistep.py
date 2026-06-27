import pytest
from clawai.planning.planner import Planner, ExecutionPlan, PlanStep

def test_create_plan_compatibility_none_steps():
    """Garante que steps=None produz um único passo baseado no objetivo (comportamento legado)."""
    planner = Planner()
    plan = planner.create_plan("Objective")
    
    assert len(plan.steps) == 1
    assert plan.steps[0].id == "step-1"
    assert plan.steps[0].description == "Objective"
    assert plan.steps[0].status == "pending"

def test_create_plan_single_step_list():
    """Garante que steps=['A'] produz exatamente um passo a partir da lista."""
    planner = Planner()
    plan = planner.create_plan("Objective", ["Step A"])
    
    assert len(plan.steps) == 1
    assert plan.steps[0].id == "step-1"
    assert plan.steps[0].description == "Step A"
    assert plan.steps[0].status == "pending"

def test_create_plan_multiple_steps_list():
    """Garante que steps=['A','B','C'] produz exatamente três passos."""
    planner = Planner()
    plan = planner.create_plan("Objective", ["Step A", "Step B", "Step C"])
    
    assert len(plan.steps) == 3
    # step 1
    assert plan.steps[0].id == "step-1"
    assert plan.steps[0].description == "Step A"
    assert plan.steps[0].status == "pending"
    # step 2
    assert plan.steps[1].id == "step-2"
    assert plan.steps[1].description == "Step B"
    assert plan.steps[1].status == "pending"
    # step 3
    assert plan.steps[2].id == "step-3"
    assert plan.steps[2].description == "Step C"
    assert plan.steps[2].status == "pending"

def test_different_creation_modes():
    """Garante que criar via objective vs criar via steps gera planos distintos."""
    planner = Planner()
    plan_legacy = planner.create_plan("Obj")
    plan_list = planner.create_plan("Obj", ["A"])

    assert len(plan_legacy.steps) == 1
    assert len(plan_list.steps) == 1
    # Os planos devem ser diferentes pois representam modos distintos de criação
    assert plan_legacy != plan_list

def test_create_plan_validation():
    planner = Planner()
    
    # steps como string deve gerar ValueError
    with pytest.raises(ValueError):
        planner.create_plan("Obj", "string")
        
    # steps vazio
    with pytest.raises(ValueError):
        planner.create_plan("Obj", [])

    # steps com tipos inválidos
    with pytest.raises(ValueError):
        planner.create_plan("Obj", [123])
    with pytest.raises(ValueError):
        planner.create_plan("Obj", [{"a": 1}])
    with pytest.raises(ValueError):
        planner.create_plan("Obj", [True])
    with pytest.raises(ValueError):
        planner.create_plan("Obj", [None])

    # descrições vazias ou espaços
    with pytest.raises(ValueError):
        planner.create_plan("Obj", [""])
    with pytest.raises(ValueError):
        planner.create_plan("Obj", ["   "])

def test_determinism():
    planner = Planner()
    plan1 = planner.create_plan("Obj", ["A", "B"])
    plan2 = planner.create_plan("Obj", ["A", "B"])
    assert plan1 == plan2

def test_multistep_execution_flow():
    planner = Planner()
    plan = planner.create_plan("Obj", ["Step 1", "Step 2"])
    
    # First step
    step1 = planner.next_step(plan)
    assert step1.id == "step-1"
    
    # Complete first, check second
    plan = planner.complete_step(plan, "step-1")
    step2 = planner.next_step(plan)
    assert step2.id == "step-2"
    
    # Complete second, check end
    plan = planner.complete_step(plan, "step-2")
    assert planner.next_step(plan) is None
