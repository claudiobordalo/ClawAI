from __future__ import annotations

from clawai.retrieval import PathMatcher


def test_path_matcher_rules() -> None:
    files = (
        "planning/planner.py",
        "agent/agent_loop.py",
        "filesystem/fs.py",
        "workspace/state.py",
    )
    m = PathMatcher()

    # equality
    eq = m.match(files, "planner.py")
    assert eq[0] == "planning/planner.py"

    # prefix
    px = m.match(files, "plan")
    assert px[0] == "planning/planner.py"

    # suffix
    sx = m.match(files, "state.py")
    assert sx[0] == "workspace/state.py"

    # contains
    ct = m.match(files, "agent")
    assert ct[0] == "agent/agent_loop.py"


def test_path_matcher_multiple_and_ordering() -> None:
    files = (
        "pkg/planner.py",
        "planning/planning_utils.py",
        "planning/planner.py",
        "plans/plan.md",
    )
    m = PathMatcher()

    # 'planner.py' equality should come first; among equals, lexicographic order
    res = m.match(files, "planner.py")
    assert res[0] == "planning/planner.py"
    assert res[1] == "pkg/planner.py"

    # contains returns all containing 'plan' ordered by rule score then path
    res2 = m.match(files, "plan")
    assert res2[0] == "planning/planner.py"
    assert res2[-1] == "plans/plan.md"
