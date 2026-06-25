from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from clawai.execution.action_executor import ActionExecutor
from clawai.tools.tool_executor import ToolExecutor


def _assert_contract(res: dict[str, Any]) -> None:
    assert set(res.keys()) == {"success", "tool", "result", "error", "duration_ms"}
    assert isinstance(res["success"], bool)
    assert res["duration_ms"] >= 0
    assert res["error"] is None or isinstance(res["error"], str)


def test_action_tool_success_propagates_tool_executor_contract() -> None:
    tool_executor = MagicMock(spec=ToolExecutor)
    expected = {
        "success": True,
        "tool": "filesystem.read_file",
        "result": {"ok": True},
        "error": None,
        "duration_ms": 1.23,
    }
    tool_executor.execute.return_value = expected

    ex = ActionExecutor(tool_executor=tool_executor)

    action = {
        "type": "tool",
        "tool": "filesystem.read_file",
        "arguments": {"path": "a.txt"},
    }

    res = ex.execute(action)
    _assert_contract(res)

    # contrato deve ser propagado exatamente pelo ActionExecutor
    assert res == expected
    tool_executor.execute.assert_called_once_with(
        tool_name="filesystem.read_file",
        arguments={"path": "a.txt"},
    )


def test_action_tool_missing_required_fields_returns_standard_error() -> None:
    tool_executor = MagicMock(spec=ToolExecutor)
    ex = ActionExecutor(tool_executor=tool_executor)

    # missing "tool" and "arguments"
    action = {"type": "tool"}
    res = ex.execute(action)

    _assert_contract(res)
    assert res["success"] is False
    assert res["result"] is None
    assert res["error"] is not None

    tool_executor.execute.assert_not_called()


def test_action_unsupported_type_returns_standard_error() -> None:
    tool_executor = MagicMock(spec=ToolExecutor)
    ex = ActionExecutor(tool_executor=tool_executor)

    res = ex.execute({"type": "unknown"})
    _assert_contract(res)
    assert res["success"] is False
    assert res["error"] is not None

    tool_executor.execute.assert_not_called()


def test_action_exception_in_tool_executor_is_caught_and_reported() -> None:
    tool_executor = MagicMock(spec=ToolExecutor)
    tool_executor.execute.side_effect = RuntimeError("boom")

    ex = ActionExecutor(tool_executor=tool_executor)

    action = {
        "type": "tool",
        "tool": "filesystem.read_file",
        "arguments": {"path": "a.txt"},
    }

    res = ex.execute(action)
    _assert_contract(res)

    assert res["success"] is False
    assert res["result"] is None
    assert "boom" in (res["error"] or "")

    tool_executor.execute.assert_called_once_with(
        tool_name="filesystem.read_file",
        arguments={"path": "a.txt"},
    )


def test_action_execute_invalid_action_type() -> None:
    tool_executor = MagicMock(spec=ToolExecutor)
    ex = ActionExecutor(tool_executor=tool_executor)

    res = ex.execute("not-a-dict")  # type: ignore[arg-type]
    _assert_contract(res)
    assert res["success"] is False
    tool_executor.execute.assert_not_called()
