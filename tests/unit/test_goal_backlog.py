from datetime import datetime, timezone

import pytest

from clawai.goals import Goal, GoalBacklog


@pytest.fixture
def sample_goals():
    return (
        Goal(id="g1", title="Fix A", description="d1", success_criteria="s1", priority=1),
        Goal(id="g2", title="Fix B", description="d2", success_criteria="s2", priority=2),
    )


def test_goal_backlog_creation(sample_goals):
    now = datetime.now(timezone.utc)
    bl = GoalBacklog(goals=sample_goals, created_at=now, summary="Two goals")
    assert bl.goals == sample_goals
    assert bl.created_at == now.replace(microsecond=0)
    assert bl.summary == "Two goals"


def test_goal_backlog_empty():
    now = datetime.now(timezone.utc)
    bl = GoalBacklog(goals=(), created_at=now, summary="Empty")
    assert bl.goals == ()
    assert bl.summary == "Empty"


def test_goal_backlog_defaults():
    bl = GoalBacklog()
    assert bl.goals == ()
    assert bl.created_at is None
    assert bl.summary == ""


def test_goal_backlog_immutability():
    bl = GoalBacklog(goals=(), created_at=datetime.now(timezone.utc), summary="Immutable")
    with pytest.raises(AttributeError):
        bl.summary = "changed"  # type: ignore[misc]


def test_goal_backlog_goals_immutable_tuple():
    g = Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1)
    bl = GoalBacklog(goals=(g,), created_at=datetime.now(timezone.utc), summary="One")
    with pytest.raises(TypeError):
        bl.goals[0] = g  # type: ignore[index]


def test_goal_backlog_equality():
    now = datetime.now(timezone.utc)
    g = (Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1),)
    a = GoalBacklog(goals=g, created_at=now, summary="Same")
    b = GoalBacklog(goals=g, created_at=now, summary="Same")
    assert a == b


def test_goal_backlog_hashable():
    now = datetime.now(timezone.utc)
    g = (Goal(id="g1", title="Fix", description="d", success_criteria="s", priority=1),)
    bl = GoalBacklog(goals=g, created_at=now, summary="Hash")
    s = {bl}
    assert bl in s


def test_goal_backlog_thousands():
    goals = tuple(
        Goal(id=f"g{i:04d}", title=f"Goal {i}", description="d", success_criteria="s", priority=i % 5)
        for i in range(1000)
    )
    bl = GoalBacklog(goals=goals, created_at=datetime.now(timezone.utc), summary="1000 goals")
    assert len(bl.goals) == 1000
    assert bl.goals[0].title == "Goal 0"
    assert bl.goals[-1].title == "Goal 999"


def test_goal_backlog_unicode():
    goals = (Goal(id="g1", title="üñîçødé 🎉", description="d", success_criteria="s", priority=1),)
    bl = GoalBacklog(goals=goals, created_at=datetime.now(timezone.utc), summary="Unicode")
    assert bl.goals[0].title == "üñîçødé 🎉"
