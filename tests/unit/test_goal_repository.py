import pytest

from clawai.engineering import EngineeringMemory
from clawai.goals import Goal, GoalPriority
from clawai.goals.engineering_memory_goal_repository import (
    EngineeringMemoryGoalRepository,
)


@pytest.fixture
def repo():
    return EngineeringMemoryGoalRepository(EngineeringMemory())


def test_save_and_load(repo):
    g = Goal(id="g1", title="Test", description="d", success_criteria="s", priority=1)
    repo.save(g)
    loaded = repo.load("g1")
    assert loaded == g


def test_load_nonexistent(repo):
    assert repo.load("nonexistent") is None


def test_update(repo):
    g = Goal(id="g1", title="Original", description="d", success_criteria="s", priority=1)
    repo.save(g)
    updated = Goal(id="g1", title="Updated", description="d", success_criteria="s", priority=2)
    repo.update(updated)
    assert repo.load("g1") == updated


def test_update_nonexistent_raises(repo):
    g = Goal(id="g1", title="New", description="d", success_criteria="s", priority=1)
    with pytest.raises(KeyError):
        repo.update(g)


def test_delete(repo):
    g = Goal(id="g1", title="Delete me", description="d", success_criteria="s", priority=1)
    repo.save(g)
    repo.delete("g1")
    assert repo.load("g1") is None


def test_delete_nonexistent(repo):
    repo.delete("nonexistent")  # should not raise


def test_list_empty(repo):
    assert repo.list() == tuple()


def test_list_multiple(repo):
    g1 = Goal(id="g1", title="Alpha", description="d1", success_criteria="s1", priority=1)
    g2 = Goal(id="g2", title="Beta", description="d2", success_criteria="s2", priority=2)
    repo.save(g1)
    repo.save(g2)
    result = repo.list()
    assert len(result) == 2


def test_list_sorted(repo):
    g1 = Goal(id="g1", title="Zeta", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="Alpha", description="d", success_criteria="s", priority=1)
    repo.save(g1)
    repo.save(g2)
    result = repo.list()
    assert result[0].title == "Alpha"
    assert result[1].title == "Zeta"


def test_list_sorted_by_priority(repo):
    g1 = Goal(id="g1", title="Low", description="d", success_criteria="s", priority=4)
    g2 = Goal(id="g2", title="Critical", description="d", success_criteria="s", priority=0)
    repo.save(g1)
    repo.save(g2)
    result = repo.list()
    assert result[0].title == "Critical"
    assert result[1].title == "Low"


def test_determinism(repo):
    g1 = Goal(id="g1", title="B", description="d", success_criteria="s", priority=1)
    g2 = Goal(id="g2", title="A", description="d", success_criteria="s", priority=1)
    repo.save(g1)
    repo.save(g2)
    assert repo.list() == repo.list()


def test_thousands(repo):
    for i in range(1000):
        repo.save(Goal(
            id=f"g{i:04d}",
            title=f"Goal {i}",
            description="d",
            success_criteria="s",
            priority=i % 5,
        ))
    result = repo.list()
    assert len(result) == 1000
