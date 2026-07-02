from __future__ import annotations

from clawai.autonomy.contracts import Action, ActionResult, PlannerResult, ReflectionResult, ToolContext, Permission


def test_planner_result_is_mapping_compatible() -> None:
    action = Action(id="a1", tool="filesystem", args={"action": "list_dir"})
    plan = PlannerResult(
        objective="inspect workspace",
        reasoning="start with discovery",
        expected_result="workspace summary",
        continue_=True,
        actions=[action],
    )

    assert plan["actions"][0].tool == "filesystem"
    assert plan.get("objective") == "inspect workspace"
    assert plan.to_dict()["actions"][0]["id"] == "a1"


def test_reflection_and_action_result_are_typed() -> None:
    result = ActionResult(action_id="a1", success=True, tool="filesystem", result={"ok": True}, error=None)
    reflection = ReflectionResult(reflection="continue", should_continue=True, error_type=None, needs_retry=False)

    assert result.success is True
    assert reflection.should_continue is True


def test_tool_context_accepts_typed_permissions() -> None:
    permission = Permission(name="filesystem.read", allowed=True, reason="local workspace")
    context = ToolContext(workspace="/tmp", permissions={"filesystem.read": permission})

    assert context.permissions["filesystem.read"].allowed is True
