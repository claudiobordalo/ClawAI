"""Edge-case tests to boost coverage above 95%."""
import math

import pytest

from clawai.goals import (
    GoalDecomposer,
    EngineeringMemoryGoalRepository,
    Goal,
    GoalPriority,
    GoalStatus,
    GoalProgress,
    GoalBacklog,
    GoalPlanner,
    GoalEventBus,
    GoalManager,
    ValidationError,
    GoalDependencyGraph,
    GoalDecomposer,
    GoalPrioritizer,
    PlanningContext,
    PlanningStrategy,
    RuleBasedPlanningStrategy,
    PlannerFactory,
    GoalComplexity,
    validate_backlog,
)
from clawai.goals.goal_status import (
    GoalStatus as GS,
    normalize_status,
    GOAL_STATUS_TODO,
    GOAL_STATUS_IN_PROGRESS,
    GOAL_STATUS_BLOCKED,
    GOAL_STATUS_DONE,
    GOAL_STATUS_CANCELLED,
)
from clawai.goals.goal_priority import (
    GoalPriority as GP,
    GOAL_PRIORITY_CRITICAL,
    GOAL_PRIORITY_HIGH,
    GOAL_PRIORITY_MEDIUM,
    GOAL_PRIORITY_LOW,
    GOAL_PRIORITY_OPTIONAL,
)
from clawai.goals.goal_validator import validate_goal
from clawai.engineering import EngineeringMemory


# Goal priority edge cases
def test_goal_priority_str():
    assert str(GoalPriority.CRITICAL) == "critical"
    assert str(GoalPriority.HIGH) == "high"
    assert str(GoalPriority.OPTIONAL) == "optional"


def test_goal_status_str():
    assert str(GoalStatus.TODO) == "todo"
    assert str(GoalStatus.CANCELLED) == "cancelled"


def test_goal_status_backward_constants():
    assert GOAL_STATUS_TODO == GoalStatus.TODO
    assert GOAL_STATUS_IN_PROGRESS == GoalStatus.IN_PROGRESS
    assert GOAL_STATUS_BLOCKED == GoalStatus.BLOCKED
    assert GOAL_STATUS_DONE == GoalStatus.DONE
    assert GOAL_STATUS_CANCELLED == GoalStatus.CANCELLED


def test_goal_priority_backward_constants():
    assert GOAL_PRIORITY_CRITICAL == GoalPriority.CRITICAL
    assert GOAL_PRIORITY_HIGH == GoalPriority.HIGH
    assert GOAL_PRIORITY_MEDIUM == GoalPriority.MEDIUM
    assert GOAL_PRIORITY_LOW == GoalPriority.LOW
    assert GOAL_PRIORITY_OPTIONAL == GoalPriority.OPTIONAL


def test_goal_priority_from_int():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=0)
    assert g.priority == GoalPriority.CRITICAL


def test_goal_priority_from_str_digit():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority="3")
    assert g.priority == GoalPriority.LOW


def test_goal_invalid_priority_raises():
    with pytest.raises(ValueError, match="Invalid priority"):
        Goal(id="g1", title="t", description="d", success_criteria="s", priority="abc")


def test_goal_bool_priority_raises():
    with pytest.raises(ValueError):
        Goal(id="g1", title="t", description="d", success_criteria="s", priority=True)


# GoalProgress edge cases
def test_goal_progress_positive_inf():
    with pytest.raises(ValueError, match="completion must not be infinite"):
        GoalProgress(goal=None, completion=float("inf"))


# GoalPlanner fallback
def test_planner_long_single_line():
    planner = GoalPlanner()
    backlog = planner.plan("long-single-objective-without-newlines")
    assert len(backlog.goals) == 1


def test_planner_with_context():
    planner = GoalPlanner()
    ctx = PlanningContext(objective="Deploy to prod")
    backlog = planner.plan("Deploy to prod", context=ctx)
    assert len(backlog.goals) == 1


# GoalStatus normalization edge cases
def test_normalize_status_by_value_string():
    result = normalize_status("todo")
    assert result == GoalStatus.TODO


def test_normalize_status_by_enum():
    result = normalize_status(GS.DONE)
    assert result == GoalStatus.DONE


def test_normalize_status_invalid():
    with pytest.raises(ValueError, match="Invalid status"):
        normalize_status("bogus_status")


# GoalValidator edge cases
def test_validate_valid_goal_no_existing():
    g = Goal(id="v1", title="Valid Goal", description="desc", success_criteria="criteria", priority=2)
    validate_goal(g)


def test_goal_manager_event_bus_injection():
    mem = EngineeringMemory()
    bus = GoalEventBus()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem), event_bus=bus)
    assert mgr is not None


def test_goal_event_bus_emit_returns_event():
    bus = GoalEventBus()
    event = bus.emit("test.event", "g1")
    assert event.event_type == "test.event"
    assert event.goal_id == "g1"


# Additional planner edge cases
def test_planner_empty_lines():
    planner = GoalPlanner()
    backlog = planner.plan("  \n  \n  ")
    assert backlog.goals == ()


def test_planner_same_line_dedup():
    planner = GoalPlanner()
    backlog = planner.plan("Fix bug\nFix bug\nFix bug")
    assert len(backlog.goals) == 1
    assert backlog.goals[0].title == "Fix bug"


# GoalValidator full coverage
def test_validate_goal_empty_id():
    with pytest.raises(ValueError, match="Goal id must not be empty"):
        Goal(id="", title="t", description="d", success_criteria="s", priority=2)


# GoalManager edge cases
def test_goal_manager_determinism_after_operations():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    g = Goal(id="g1", title="Test", description="d", success_criteria="s", priority=GoalPriority.MEDIUM)
    mgr.add_goal(g)
    mgr.complete_goal("g1")
    bl1 = mgr.create_backlog()
    bl2 = mgr.create_backlog()
    # goals and summary are deterministic; created_at differs by milliseconds
    assert bl1.goals == bl2.goals
    assert bl1.summary == bl2.summary


def test_goal_manager_fail_goal_events():
    mem = EngineeringMemory()
    bus = GoalEventBus()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem), event_bus=bus)
    mgr.add_goal(Goal(id="g1", title="Fail me", description="d", success_criteria="s", priority=2))
    bus.clear()
    result = mgr.fail_goal("g1")
    assert result is not None
    assert result.status == GoalStatus.BLOCKED


# === Sprint 3: GoalDependencyGraph ===

def test_dependency_graph_empty():
    g = GoalDependencyGraph(())
    assert not g.has_cycle()
    assert g.topological_sort() == ()


def test_dependency_graph_no_deps():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1)
    graph = GoalDependencyGraph((g1, g2))
    assert not graph.has_cycle()
    assert len(graph.topological_sort()) == 2


def test_dependency_graph_linear_deps():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1, depends_on=("g1",))
    g3 = Goal(id="g3", title="t3", description="d", success_criteria="s", priority=1, depends_on=("g2",))
    graph = GoalDependencyGraph((g1, g2, g3))
    assert not graph.has_cycle()
    order = graph.topological_sort()
    assert [g.id for g in order] == ["g1", "g2", "g3"]


def test_dependency_graph_cycle_detection():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1, depends_on=("g2",))
    g2 = Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1, depends_on=("g1",))
    graph = GoalDependencyGraph((g1, g2))
    assert graph.has_cycle()
    assert graph.topological_sort() == ()
    cycle = graph.find_cycle()
    assert len(cycle) >= 2


def test_dependency_graph_unblocked():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1, depends_on=("g1",))
    graph = GoalDependencyGraph((g1, g2))
    unblocked = graph.get_unblocked()
    assert len(unblocked) == 1
    assert unblocked[0].id == "g1"


def test_dependency_graph_dependents():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1, depends_on=("g1",))
    graph = GoalDependencyGraph((g1, g2))
    assert graph.get_dependents("g1") == ("g2",)
    assert graph.get_dependents("g2") == ()


def test_dependency_graph_depth():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1, depends_on=("g1",))
    g3 = Goal(id="g3", title="t3", description="d", success_criteria="s", priority=1, depends_on=("g2",))
    graph = GoalDependencyGraph((g1, g2, g3))
    assert graph.dependency_depth("g1") == 0
    assert graph.dependency_depth("g2") == 1
    assert graph.dependency_depth("g3") == 2


# === Sprint 3: GoalPrioritizer ===

def test_prioritizer_basic():
    g1 = Goal(id="g1", title="Low prio", description="d", success_criteria="s", priority=GoalPriority.LOW)
    g2 = Goal(id="g2", title="High prio", description="d", success_criteria="s", priority=GoalPriority.HIGH)
    graph = GoalDependencyGraph((g1, g2))
    p = GoalPrioritizer(graph)
    ordered = p.prioritize((g1, g2))
    assert ordered[0].id == "g2"
    assert ordered[1].id == "g1"


def test_prioritizer_preserves_input_order():
    g1 = Goal(id="g1", title="A", description="d", success_criteria="s", priority=GoalPriority.MEDIUM)
    g2 = Goal(id="g2", title="B", description="d", success_criteria="s", priority=GoalPriority.MEDIUM)
    g3 = Goal(id="g3", title="C", description="d", success_criteria="s", priority=GoalPriority.MEDIUM)
    graph = GoalDependencyGraph((g1, g2, g3))
    p = GoalPrioritizer(graph)
    ordered = p.prioritize((g1, g2, g3))
    assert [g.id for g in ordered] == ["g1", "g2", "g3"]


# === Sprint 3: GoalDecomposer ===

def test_decomposer_empty():
    d = GoalDecomposer()
    assert d.decompose("") == ()
    assert d.decompose("   ") == ()


def test_decomposer_single_line():
    d = GoalDecomposer()
    goals = d.decompose("Add OAuth")
    assert len(goals) == 1
    assert goals[0].title == "Add OAuth"


def test_decomposer_multiple_lines():
    d = GoalDecomposer()
    goals = d.decompose("Setup auth\nCreate login page\nAdd logout")
    assert len(goals) == 3


def test_decomposer_deduplicates():
    d = GoalDecomposer()
    goals = d.decompose("Fix bug\nFix bug\nAdd feature")
    assert len(goals) == 2


def test_decomposer_infers_complexity():
    d = GoalDecomposer()
    simple = d.decompose("Simple change")
    complex = d.decompose("Complex refactoring")
    assert simple[0].estimated_complexity == "XS"
    assert complex[0].estimated_complexity == "L"


def test_decomposer_infers_tags():
    d = GoalDecomposer()
    backend = d.decompose("Add API endpoint")
    frontend = d.decompose("Create UI component")
    tests = d.decompose("Write unit tests")
    assert "backend" in backend[0].tags
    assert "frontend" in frontend[0].tags
    assert "tests" in tests[0].tags


def test_decomposer_deterministic():
    d = GoalDecomposer()
    a = d.decompose("Deploy API\nWrite tests")
    b = d.decompose("Deploy API\nWrite tests")
    assert a == b


# === Sprint 3: PlanningContext ===

def test_planning_context_defaults():
    ctx = PlanningContext(objective="Test")
    assert ctx.objective == "Test"
    assert ctx.repository_state == []
    assert ctx.available_tools == []
    assert ctx.previous_attempts == 0
    assert ctx.active_branch == ""


# === Sprint 3: PlanningStrategy / RuleBasedPlanningStrategy ===

def test_rule_based_strategy():
    strategy = RuleBasedPlanningStrategy(decomposer=GoalDecomposer())
    ctx = PlanningContext(objective="Fix bug\nWrite tests")
    backlog = strategy.plan(ctx)
    assert len(backlog.goals) == 2


def test_rule_based_strategy_empty_objective():
    strategy = RuleBasedPlanningStrategy(decomposer=GoalDecomposer())
    ctx = PlanningContext(objective="")
    backlog = strategy.plan(ctx)
    assert backlog.goals == ()
    assert "No goals" in backlog.summary


# === Sprint 3: PlannerFactory ===

def test_planner_factory_default():
    strategy = PlannerFactory.create()
    assert isinstance(strategy, RuleBasedPlanningStrategy)


def test_planner_factory_unknown():
    with pytest.raises(ValueError, match="Unknown strategy"):
        PlannerFactory.create("nonexistent")


def test_planner_factory_register():
    class TestStrategy(PlanningStrategy):
        def plan(self, context):
            from clawai.goals import GoalBacklog
            from datetime import datetime, timezone
            return GoalBacklog(goals=(), created_at=datetime.now(timezone.utc), summary="test")

    PlannerFactory.register("test", TestStrategy)
    strategy = PlannerFactory.create("test")
    assert isinstance(strategy, TestStrategy)


# === Sprint 3: GoalValidator validate_backlog ===

def test_validate_backlog_empty():
    with pytest.raises(ValidationError) as exc:
        validate_backlog(())
    assert "Backlog must not be empty" in exc.value.errors


def test_validate_backlog_duplicate_titles():
    g1 = Goal(id="g1", title="Same", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="Same", description="d", success_criteria="s", priority=1)
    with pytest.raises(ValidationError) as exc:
        validate_backlog((g1, g2))
    assert any("Duplicate goal title" in e for e in exc.value.errors)


def test_validate_backlog_nonexistent_dep():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1, depends_on=("nonexistent",))
    with pytest.raises(ValidationError) as exc:
        validate_backlog((g1,))
    assert any("non-existent goal" in e for e in exc.value.errors)


def test_validate_backlog_cycle():
    g1 = Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1, depends_on=("g2",))
    g2 = Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1, depends_on=("g1",))
    with pytest.raises(ValidationError) as exc:
        validate_backlog((g1, g2))
    assert any("cycle" in e for e in exc.value.errors)


# === Sprint 3: GoalComplexity ===

def test_goal_complexity_values():
    assert GoalComplexity.XS == 0
    assert GoalComplexity.S == 1
    assert GoalComplexity.M == 2
    assert GoalComplexity.L == 3
    assert GoalComplexity.XL == 4


def test_goal_complexity_str():
    assert str(GoalComplexity.XS) == "XS"
    assert str(GoalComplexity.XL) == "XL"


# === Sprint 3: PlannerFactory integration with GoalPlanner ===

def test_goal_planner_with_strategy_name():
    planner = GoalPlanner(strategy="rule_based")
    backlog = planner.plan("Fix bug")
    assert len(backlog.goals) == 1


# === Sprint 3: Large backlog ===

def test_decomposer_large_input():
    lines = "\n".join([f"Task {i}" for i in range(100)])
    d = GoalDecomposer()
    goals = d.decompose(lines)
    assert len(goals) == 100


# === Sprint 3: Unicode and emoji in decomposition ===

def test_decomposer_unicode():
    d = GoalDecomposer()
    goals = d.decompose("Adicionar OAuth\nCriar testes\nAtualizar docs")
    assert len(goals) == 3
    assert goals[0].title == "Adicionar OAuth"


def test_decomposer_emoji():
    d = GoalDecomposer()
    goals = d.decompose("🎯 Fix target\n🚀 Launch feature")
    assert len(goals) == 2
