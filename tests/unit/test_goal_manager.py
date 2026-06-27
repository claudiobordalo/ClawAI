from datetime import datetime, timezone

import pytest

from clawai.engineering import EngineeringMemory, EngineeringRecord
from clawai.goals import (
    Goal,
    GoalBacklog,
    GoalManager,
    GoalProgress,
    GoalPriority,
    GoalStatus,
)
from clawai.goals.goal_events import GoalEventBus
from clawai.goals.engineering_memory_goal_repository import (
    EngineeringMemoryGoalRepository,
)


def _rec(objective: str, diagnosis: str, success: bool) -> EngineeringRecord:
    return EngineeringRecord(
        timestamp=datetime.now(timezone.utc),
        objective=objective,
        target_query="t",
        instructions="i",
        diagnosis=diagnosis,
        strategy="RepairStrategy",
        summary="sum",
        success=success,
        modified_files=("a.py",) if success else tuple(),
        failed_tests=tuple() if success else ("t::a",),
        duration=0.5,
    )


def _goal(
    gid: str,
    title: str,
    priority: int = 2,
    status: str = "todo",
) -> Goal:
    return Goal(
        id=gid,
        title=title,
        description="desc",
        success_criteria="criteria",
        priority=priority,
        status=status,
    )


# --- Empty backlog ---

def test_create_backlog_empty():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert isinstance(bl, GoalBacklog)
    assert bl.goals == ()


def test_next_goal_no_backlog():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr.next_goal() is None


def test_next_goal_empty_backlog():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    assert mgr.next_goal() is None


# --- Single goal from memory ---

def test_create_backlog_single_pending():
    mem = EngineeringMemory()
    mem.add(_rec("Fix login", "Failed auth", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 1
    g = bl.goals[0]
    assert g.title == "Fix login"
    assert g.status == GoalStatus.TODO


def test_create_backlog_single_completed():
    mem = EngineeringMemory()
    mem.add(_rec("Fix login", "All good", True))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 1
    g = bl.goals[0]
    assert g.title == "Fix login"
    assert g.status == GoalStatus.DONE


def test_create_backlog_skip_completed():
    mem = EngineeringMemory()
    mem.add(_rec("Fix login", "All good", True))
    mem.add(_rec("Fix db", "Failed", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 2
    g_login = next(g for g in bl.goals if g.title == "Fix login")
    g_db = next(g for g in bl.goals if g.title == "Fix db")
    assert g_login.status == GoalStatus.DONE
    assert g_db.status == GoalStatus.TODO


def test_create_backlog_multiple():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "Failed A", False))
    mem.add(_rec("Fix B", "Failed B", False))
    mem.add(_rec("Fix C", "OK C", True))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 3


# --- Deduplication ---

def test_create_backlog_deduplicates():
    mem = EngineeringMemory()
    mem.add(_rec("Fix login", "Failed", False))
    mem.add(_rec("Fix login", "Failed again", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 1
    assert bl.goals[0].title == "Fix login"


def test_create_backlog_deduplicates_case_insensitive():
    mem = EngineeringMemory()
    mem.add(_rec("Fix login", "Failed", False))
    mem.add(_rec("FIX LOGIN", "Failed again", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 1


# --- Sorting ---

def test_create_backlog_sort_priority():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "fail", False))
    mem.add(_rec("Fix A", "fail", False))
    mem.add(_rec("Fix B", "fail", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 2
    # Fix A: 2 fails -> CRITICAL (0), Fix B: 1 fail -> HIGH (1)
    assert bl.goals[0].title == "Fix A"
    assert bl.goals[1].title == "Fix B"


def test_create_backlog_sort_title():
    mem = EngineeringMemory()
    mem.add(_rec("Beta", "fail", False))
    mem.add(_rec("Alpha", "fail", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert len(bl.goals) == 2
    assert bl.goals[0].title == "Alpha"
    assert bl.goals[1].title == "Beta"


def test_create_backlog_sort_title_case_insensitive():
    mem = EngineeringMemory()
    mem.add(_rec("beta", "fail", False))
    mem.add(_rec("Alpha", "fail", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl = mgr.create_backlog()
    assert bl.goals[0].title == "Alpha"
    assert bl.goals[1].title == "beta"


# --- next_goal ---

def test_next_goal_returns_first_pending():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "OK", True))
    mem.add(_rec("Fix B", "Failed", False))
    mem.add(_rec("Fix C", "Failed", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    g = mgr.next_goal()
    assert g is not None
    assert g.title == "Fix B"
    assert g.status == GoalStatus.TODO


def test_next_goal_all_completed():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "OK", True))
    mem.add(_rec("Fix B", "OK", True))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    assert mgr.next_goal() is None


# --- progress ---

def test_progress_no_backlog():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    gp = mgr.progress()
    assert gp.completion == 0.0
    assert gp.completed_items == ()
    assert gp.remaining_items == ()


def test_progress_empty_backlog():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    gp = mgr.progress()
    assert gp.completion == 0.0


def test_progress_all_pending():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "fail", False))
    mem.add(_rec("Fix B", "fail", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    gp = mgr.progress()
    assert gp.completion == 0.0
    assert len(gp.remaining_items) == 2


def test_progress_mixed():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "OK", True))
    mem.add(_rec("Fix B", "fail", False))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    gp = mgr.progress()
    assert gp.completion == 50.0
    assert gp.completed_items == ("Fix A",)
    assert gp.remaining_items == ("Fix B",)


def test_progress_all_completed():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "OK", True))
    mem.add(_rec("Fix B", "OK", True))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    gp = mgr.progress()
    assert gp.completion == 100.0
    assert len(gp.completed_items) == 2
    assert gp.remaining_items == ()


# --- Determinism ---

def test_determinism_create_backlog():
    mem = EngineeringMemory()
    mem.add(_rec("Zeta", "fail", False))
    mem.add(_rec("Alpha", "fail", False))
    mem.add(_rec("Alpha", "fail", False))
    mem.add(_rec("Beta", "OK", True))
    mgr1 = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr2 = GoalManager(EngineeringMemoryGoalRepository(mem))
    bl1 = mgr1.create_backlog()
    bl2 = mgr2.create_backlog()
    assert bl1 == bl2


def test_determinism_next_goal():
    mem = EngineeringMemory()
    mem.add(_rec("Zeta", "fail", False))
    mem.add(_rec("Alpha", "fail", False))
    mgr1 = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr2 = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr1.create_backlog()
    mgr2.create_backlog()
    assert mgr1.next_goal() == mgr2.next_goal()


def test_determinism_progress():
    mem = EngineeringMemory()
    mem.add(_rec("Fix A", "OK", True))
    mem.add(_rec("Fix B", "fail", False))
    mgr1 = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr2 = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr1.create_backlog()
    mgr2.create_backlog()
    assert mgr1.progress() == mgr2.progress()


# --- GoalProgress goal field ---

def test_progress_goal_field():
    mem = EngineeringMemory()
    mem.add(_rec("Fix B", "fail", False))
    mem.add(_rec("Fix A", "OK", True))
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.create_backlog()
    gp = mgr.progress()
    assert gp.goal is not None
    assert gp.goal.title == "Fix B"
    assert gp.goal.status == GoalStatus.TODO


# --- add_goal ---

def test_add_goal():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    g = _goal("g1", "New goal")
    result = mgr.add_goal(g)
    assert result == g
    assert mgr.find_goal("g1") == g


def test_add_goal_duplicate_title():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Same title"))
    with pytest.raises(Exception):
        mgr.add_goal(_goal("g2", "Same title"))


def test_add_goal_validates():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    with pytest.raises(Exception):
        mgr.add_goal(_goal("g1", ""))


# --- complete_goal ---

def test_complete_goal():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Test goal"))
    result = mgr.complete_goal("g1")
    assert result is not None
    assert result.status == GoalStatus.DONE
    assert mgr.find_goal("g1").status == GoalStatus.DONE


def test_complete_goal_not_found():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr.complete_goal("nonexistent") is None


# --- fail_goal ---

def test_fail_goal():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Test goal"))
    result = mgr.fail_goal("g1")
    assert result is not None
    assert result.status == GoalStatus.BLOCKED


def test_fail_goal_not_found():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr.fail_goal("nonexistent") is None


# --- reprioritize ---

def test_reprioritize():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Test goal"))
    result = mgr.reprioritize("g1", GoalPriority.CRITICAL)
    assert result is not None
    assert result.priority == GoalPriority.CRITICAL


def test_reprioritize_not_found():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr.reprioritize("nonexistent", GoalPriority.HIGH) is None


def test_reprioritize_int():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Test goal"))
    result = mgr.reprioritize("g1", 0)
    assert result is not None
    assert result.priority == GoalPriority.CRITICAL


# --- find_goal ---

def test_find_goal():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Find me"))
    assert mgr.find_goal("g1") is not None
    assert mgr.find_goal("g1").title == "Find me"


def test_find_goal_not_found():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr.find_goal("nonexistent") is None


# --- remove_goal ---

def test_remove_goal():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Remove me"))
    assert mgr.remove_goal("g1") is True
    assert mgr.find_goal("g1") is None


def test_remove_goal_not_found():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr.remove_goal("nonexistent") is False


# --- update_progress ---

def test_update_progress():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Progress goal"))
    gp = mgr.update_progress("g1", 50.0)
    assert gp is not None
    assert gp.completion == 50.0
    assert gp.goal is not None
    assert gp.goal.title == "Progress goal"


def test_update_progress_complete():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    mgr.add_goal(_goal("g1", "Will complete"))
    mgr.update_progress("g1", 100.0)
    # Should auto-complete the goal
    g = mgr.find_goal("g1")
    assert g is not None
    assert g.status == GoalStatus.DONE


def test_update_progress_not_found():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr.update_progress("nonexistent", 50.0) is None


# --- Events ---

def test_goal_created_event():
    mem = EngineeringMemory()
    event_bus = GoalEventBus()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem), event_bus=event_bus)
    mgr.add_goal(_goal("g1", "Event goal"))
    events = event_bus.history()
    assert any(e.event_type == "goal.created" for e in events)
    goal_events = [e for e in events if e.event_type == "goal.created"]
    assert goal_events[0].goal_id == "g1"


def test_goal_completed_event():
    mem = EngineeringMemory()
    event_bus = GoalEventBus()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem), event_bus=event_bus)
    mgr.add_goal(_goal("g1", "Complete me"))
    event_bus.clear()
    mgr.complete_goal("g1")
    events = event_bus.history()
    assert any(e.event_type == "goal.completed" for e in events)


def test_goal_cancelled_event():
    mem = EngineeringMemory()
    event_bus = GoalEventBus()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem), event_bus=event_bus)
    mgr.add_goal(_goal("g1", "Remove me"))
    event_bus.clear()
    mgr.remove_goal("g1")
    events = event_bus.history()
    assert any(e.event_type == "goal.cancelled" for e in events)


def test_goal_progress_event():
    mem = EngineeringMemory()
    event_bus = GoalEventBus()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem), event_bus=event_bus)
    mgr.add_goal(_goal("g1", "Progress"))
    event_bus.clear()
    mgr.update_progress("g1", 75.0)
    events = event_bus.history()
    assert any(e.event_type == "goal.progress_updated" for e in events)


# --- Repository injection ---

def test_goal_manager_with_repository():
    mem = EngineeringMemory()
    repo = EngineeringMemoryGoalRepository(mem)
    mgr = GoalManager(repository=repo)
    g = _goal("g1", "Repo test")
    mgr.add_goal(g)
    assert mgr.find_goal("g1") == g


# --- Concurrency ---

def test_concurrent_add_and_complete():
    import threading
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    errors: list = []

    def worker(gid: str, title: str):
        try:
            mgr.add_goal(_goal(gid, title))
            mgr.complete_goal(gid)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(f"g{i}", f"Task {i}")) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


# --- Thousands of goals ---

def test_thousands_of_goals_deterministic():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    for i in range(1000):
        mgr.add_goal(_goal(f"g{i:04d}", f"Goal {i}", priority=i % 5))
    backlog = mgr.create_backlog()
    assert len(backlog.goals) == 1000
    # Verify ordering
    for i in range(999):
        assert backlog.goals[i].priority.value <= backlog.goals[i + 1].priority.value


# --- Backward compatibility ---

def test_backward_compat_engineering_memory_constructor():
    mem = EngineeringMemory()
    mgr = GoalManager(EngineeringMemoryGoalRepository(mem))
    assert mgr is not None
    g = _goal("g1", "Compat")
    mgr.add_goal(g)
    assert mgr.find_goal("g1") == g
    # next_goal() auto-creates backlog which includes added goals
    next_g = mgr.next_goal()
    assert next_g is not None
    assert next_g.title == "Compat"
