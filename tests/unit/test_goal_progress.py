import math

import pytest

from clawai.goals import Goal, GoalProgress


@pytest.fixture
def sample_goal():
    return Goal(
        id="g1",
        title="Fix login",
        description="Implement login flow",
        success_criteria="All auth tests pass",
        priority=1,
    )


def test_goal_progress_creation(sample_goal):
    gp = GoalProgress(
        goal=sample_goal,
        completion=50.0,
        completed_items=("item1",),
        remaining_items=("item2",),
        summary="Half done",
    )
    assert gp.goal == sample_goal
    assert gp.completion == 50.0
    assert gp.completed_items == ("item1",)
    assert gp.remaining_items == ("item2",)
    assert gp.summary == "Half done"


def test_goal_progress_completion_zero():
    gp = GoalProgress(
        goal=None,
        completion=0.0,
        completed_items=(),
        remaining_items=("item1", "item2"),
        summary="Not started",
    )
    assert gp.completion == 0.0


def test_goal_progress_completion_hundred():
    gp = GoalProgress(
        goal=None,
        completion=100.0,
        completed_items=("item1", "item2"),
        remaining_items=(),
        summary="All done",
    )
    assert gp.completion == 100.0


def test_goal_progress_completion_percentage():
    gp = GoalProgress(
        goal=None,
        completion=33.33,
        completed_items=("item1",),
        remaining_items=("item2", "item3"),
        summary="33.33% complete",
    )
    assert gp.completion == 33.33


def test_goal_progress_invalid_completion_negative():
    with pytest.raises(ValueError, match="completion must be >= 0.0"):
        GoalProgress(
            goal=None,
            completion=-1.0,
            completed_items=(),
            remaining_items=("item",),
            summary="Invalid",
        )


def test_goal_progress_invalid_completion_over():
    with pytest.raises(ValueError, match="completion must be <= 100.0"):
        GoalProgress(
            goal=None,
            completion=100.1,
            completed_items=(),
            remaining_items=("item",),
            summary="Invalid",
        )


def test_goal_progress_immutability(sample_goal):
    gp = GoalProgress(
        goal=sample_goal,
        completion=50.0,
        completed_items=(),
        remaining_items=(),
        summary="test",
    )
    with pytest.raises(AttributeError):
        gp.completion = 75.0  # type: ignore[misc]


def test_goal_progress_empty_items():
    gp = GoalProgress(
        goal=None,
        completion=0.0,
        completed_items=(),
        remaining_items=(),
        summary="Empty backlog",
    )
    assert gp.completed_items == ()
    assert gp.remaining_items == ()


def test_goal_progress_is_completed():
    gp = GoalProgress(goal=None, completion=100.0)
    assert gp.is_completed is True
    gp2 = GoalProgress(goal=None, completion=50.0)
    assert gp2.is_completed is False


def test_goal_progress_remaining_percentage():
    gp = GoalProgress(goal=None, completion=30.0)
    assert gp.remaining_percentage == 70.0
    gp2 = GoalProgress(goal=None, completion=100.0)
    assert gp2.remaining_percentage == 0.0


def test_goal_progress_completed_percentage():
    gp = GoalProgress(goal=None, completion=75.5)
    assert gp.completed_percentage == 75.5


def test_goal_progress_nan():
    with pytest.raises(ValueError, match="completion must not be NaN"):
        GoalProgress(goal=None, completion=math.nan)


def test_goal_progress_inf():
    with pytest.raises(ValueError, match="completion must not be infinite"):
        GoalProgress(goal=None, completion=math.inf)


def test_goal_progress_neg_inf():
    with pytest.raises(ValueError, match="completion must not be infinite"):
        GoalProgress(goal=None, completion=-math.inf)


def test_goal_progress_edge_cases():
    gp = GoalProgress(goal=None, completion=0.0)
    assert gp.is_completed is False
    assert gp.remaining_percentage == 100.0
    gp2 = GoalProgress(goal=None, completion=100.0)
    assert gp2.is_completed is True
    assert gp2.remaining_percentage == 0.0


def test_goal_progress_defaults():
    gp = GoalProgress(goal=None, completion=0.0)
    assert gp.completed_items == ()
    assert gp.remaining_items == ()
    assert gp.summary == ""
