from clawai.goals import GoalPlanner, GoalBacklog, PlanningContext
from clawai.goals.goal_status import GoalStatus


def test_planner_empty():
    planner = GoalPlanner()
    backlog = planner.plan("")
    assert isinstance(backlog, GoalBacklog)
    assert backlog.goals == ()


def test_planner_whitespace():
    planner = GoalPlanner()
    backlog = planner.plan("   ")
    assert backlog.goals == ()


def test_planner_single_line():
    planner = GoalPlanner()
    backlog = planner.plan("Add OAuth")
    assert len(backlog.goals) == 1
    assert backlog.goals[0].title == "Add OAuth"
    assert backlog.goals[0].status == GoalStatus.TODO


def test_planner_multiple_lines():
    planner = GoalPlanner()
    backlog = planner.plan("Setup auth\nCreate login page\nAdd logout")
    assert len(backlog.goals) == 3
    assert backlog.goals[0].title == "Setup auth"
    assert backlog.goals[1].title == "Create login page"
    assert backlog.goals[2].title == "Add logout"


def test_planner_deduplicates():
    planner = GoalPlanner()
    backlog = planner.plan("Fix bug\nFix bug\nAdd feature")
    assert len(backlog.goals) == 2
    assert backlog.goals[0].title == "Fix bug"
    assert backlog.goals[1].title == "Add feature"


def test_planner_deterministic():
    planner = GoalPlanner()
    a = planner.plan("Deploy API\nWrite tests")
    b = planner.plan("Deploy API\nWrite tests")
    assert a.goals == b.goals


def test_planner_has_goals():
    planner = GoalPlanner()
    backlog = planner.plan("Setup monitoring")
    assert len(backlog.goals) == 1
    g = backlog.goals[0]
    assert g.success_criteria == "Setup monitoring completed successfully"
    assert g.description.startswith("Decomposed from:")


def test_planner_backward_compat_via_context():
    planner = GoalPlanner()
    ctx = PlanningContext(objective="Fix bug")
    backlog = planner.plan("Fix bug", context=ctx)
    assert len(backlog.goals) == 1


def test_planner_plan_to_goals():
    planner = GoalPlanner()
    goals = planner.plan_to_goals("Add auth\nWrite tests")
    assert len(goals) == 2
