import pytest

from clawai.goals import Goal
from clawai.goals.goal import (
    GOAL_STATUS_PENDING,
    GOAL_STATUS_RUNNING,
    GOAL_STATUS_COMPLETED,
    GOAL_STATUS_FAILED,
    GOAL_STATUS_CANCELLED,
    ALLOWED_STATUSES,
)
from clawai.goals.goal_status import GoalStatus
from clawai.goals.goal_priority import GoalPriority


def test_goal_creation():
    g = Goal(
        id="g1",
        title="Fix login",
        description="Implement login flow",
        success_criteria="All auth tests pass",
        priority=1,
        status=GOAL_STATUS_PENDING,
    )
    assert g.id == "g1"
    assert g.title == "Fix login"
    assert g.description == "Implement login flow"
    assert g.success_criteria == "All auth tests pass"
    assert g.priority == 1
    assert g.priority == GoalPriority.HIGH
    assert g.status == GOAL_STATUS_PENDING


def test_goal_default_status():
    g = Goal(
        id="g1",
        title="Fix login",
        description="Implement login flow",
        success_criteria="All auth tests pass",
        priority=1,
    )
    assert g.status == GOAL_STATUS_PENDING


def test_goal_default_priority():
    g = Goal(
        id="g1",
        title="Fix login",
        description="desc",
        success_criteria="criteria",
    )
    assert g.priority == GoalPriority.MEDIUM


def test_goal_immutability():
    g = Goal(
        id="g1",
        title="Fix login",
        description="desc",
        success_criteria="criteria",
        priority=1,
    )
    with pytest.raises(AttributeError):
        g.title = "New title"  # type: ignore[misc]


def test_goal_allowed_statuses():
    for status in ALLOWED_STATUSES:
        g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, status=status)
        assert g.status == status


def test_goal_invalid_status():
    with pytest.raises(ValueError, match="Invalid status"):
        Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, status="unknown")


def test_goal_equality():
    a = Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1)
    b = Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1)
    assert a == b


def test_goal_inequality():
    a = Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1)
    b = Goal(id="g2", title="Fix", description="d", success_criteria="s", priority=1)
    assert a != b


def test_goal_hashable():
    g = Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1)
    s = {g}
    assert g in s


def test_goal_repr():
    g = Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1)
    r = repr(g)
    assert "Goal" in r
    assert "g1" in r
    assert "Fix" in r


def test_goal_empty_title():
    with pytest.raises(ValueError, match="Goal title must not be empty"):
        Goal(id="g1", title="", description="d", success_criteria="s", priority=1)


def test_goal_empty_id():
    with pytest.raises(ValueError, match="Goal id must not be empty"):
        Goal(id="", title="t", description="d", success_criteria="s", priority=1)


def test_goal_empty_success_criteria():
    with pytest.raises(ValueError, match="Goal success_criteria must not be empty"):
        Goal(id="g1", title="t", description="d", success_criteria="", priority=1)


def test_goal_empty_description():
    with pytest.raises(ValueError, match="Goal description must not be empty"):
        Goal(id="g1", title="t", description="", success_criteria="s", priority=1)


def test_goal_backward_compat_string_status():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, status="pending")
    assert g.status == GoalStatus.TODO
    g2 = Goal(id="g2", title="t", description="d", success_criteria="s", priority=1, status="running")
    assert g2.status == GoalStatus.IN_PROGRESS
    g3 = Goal(id="g3", title="t", description="d", success_criteria="s", priority=1, status="completed")
    assert g3.status == GoalStatus.DONE
    g4 = Goal(id="g4", title="t", description="d", success_criteria="s", priority=1, status="failed")
    assert g4.status == GoalStatus.BLOCKED
    g5 = Goal(id="g5", title="t", description="d", success_criteria="s", priority=1, status="cancelled")
    assert g5.status == GoalStatus.CANCELLED


def test_goal_with_unicode():
    g = Goal(id="g1", title="Coração 🔥", description="teste üñîçødé", success_criteria="✓", priority=1)
    assert g.title == "Coração 🔥"
    assert g.description == "teste üñîçødé"
    assert g.success_criteria == "✓"


def test_goal_with_emoji():
    g = Goal(id="g1", title="🎯 Target", description="🚀 Launch", success_criteria="✅ Done", priority=1)
    assert g.title == "🎯 Target"
    assert g.description == "🚀 Launch"
    assert g.success_criteria == "✅ Done"


def test_goal_status_comparison():
    assert GoalStatus.TODO.value == "todo"
    assert GoalStatus.IN_PROGRESS.value == "in_progress"
    assert GoalStatus.BLOCKED.value == "blocked"
    assert GoalStatus.DONE.value == "done"
    assert GoalStatus.CANCELLED.value == "cancelled"


def test_goal_priority_values():
    assert GoalPriority.CRITICAL.value == 0
    assert GoalPriority.HIGH.value == 1
    assert GoalPriority.MEDIUM.value == 2
    assert GoalPriority.LOW.value == 3
    assert GoalPriority.OPTIONAL.value == 4


def test_goal_priority_comparison():
    assert GoalPriority.CRITICAL < GoalPriority.HIGH
    assert GoalPriority.HIGH < GoalPriority.MEDIUM
    assert GoalPriority.MEDIUM < GoalPriority.LOW
    assert GoalPriority.LOW < GoalPriority.OPTIONAL
    assert GoalPriority.CRITICAL == 0
    assert GoalPriority.HIGH == 1


def test_goal_priority_ordering():
    g1 = Goal(id="g1", title="critical", description="d", success_criteria="s", priority=GoalPriority.CRITICAL)
    g2 = Goal(id="g2", title="high", description="d", success_criteria="s", priority=GoalPriority.HIGH)
    g3 = Goal(id="g3", title="medium", description="d", success_criteria="s", priority=GoalPriority.MEDIUM)
    assert g1.priority < g2.priority < g3.priority


def test_goal_invalid_id_type():
    with pytest.raises(ValueError):
        Goal(id="", title="t", description="d", success_criteria="s", priority=1)


def test_goal_depends_on_default():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1)
    assert g.depends_on == ()


def test_goal_depends_on_explicit():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, depends_on=("g0",))
    assert g.depends_on == ("g0",)


def test_goal_estimated_complexity_default():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1)
    assert g.estimated_complexity == "M"


def test_goal_estimated_complexity_valid():
    for val in ("XS", "S", "M", "L", "XL"):
        g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, estimated_complexity=val)
        assert g.estimated_complexity == val


def test_goal_estimated_complexity_lowercase():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, estimated_complexity="xs")
    assert g.estimated_complexity == "XS"


def test_goal_estimated_complexity_invalid():
    with pytest.raises(ValueError, match="Invalid estimated_complexity"):
        Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, estimated_complexity="XXL")


def test_goal_tags_default():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1)
    assert g.tags == ()


def test_goal_tags_explicit():
    g = Goal(id="g1", title="t", description="d", success_criteria="s", priority=1, tags=("backend", "security"))
    assert g.tags == ("backend", "security")
