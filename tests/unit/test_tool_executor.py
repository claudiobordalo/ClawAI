from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from clawai.tools.tool_executor import ToolExecutor
from clawai.tools.tool_registry import ToolRegistry


def _assert_contract(res: dict[str, Any], *, tool: str | None) -> None:
    assert set(res.keys()) == {"success", "tool", "result", "error", "duration_ms"}
    assert isinstance(res["success"], bool)
    assert res["duration_ms"] >= 0
    if tool is not None:
        assert res["tool"] == tool
    assert res["error"] is None or isinstance(res["error"], str)


def test_tool_found_executes(tmp_path) -> None:
    _ = tmp_path
    registry = MagicMock(spec=ToolRegistry)

    tool = MagicMock()
    tool.execute.return_value = {"success": True, "result": 123, "error": None, "duration_ms": 1.0}

    registry.get.return_value = {
        "success": True,
        "result": tool,
        "error": None,
        "duration_ms": 1.0,
    }

    ex = ToolExecutor(registry=registry)
    res = ex.execute(tool_name="t1", arguments={"a": 1})

    _assert_contract(res, tool="t1")
    assert res["success"] is True
    assert res["result"] == 123
    assert res["error"] is None
    registry.get.assert_called_once_with("t1")
    tool.execute.assert_called_once_with(a=1)


def test_tool_inexistent(tmp_path) -> None:
    _ = tmp_path
    registry = MagicMock(spec=ToolRegistry)
    registry.get.return_value = {
        "success": False,
        "result": None,
        "error": "Tool not found: missing",
        "duration_ms": 1.0,
    }

    ex = ToolExecutor(registry=registry)
    res = ex.execute(tool_name="missing", arguments={})

    _assert_contract(res, tool="missing")
    assert res["success"] is False
    assert res["result"] is None
    assert res["error"] == "Tool not found: missing"
    registry.get.assert_called_once_with("missing")


def test_tool_raises_exception(tmp_path) -> None:
    _ = tmp_path
    registry = MagicMock(spec=ToolRegistry)

    tool = MagicMock()
    tool.execute.side_effect = RuntimeError("boom")

    registry.get.return_value = {
        "success": True,
        "result": tool,
        "error": None,
        "duration_ms": 1.0,
    }

    ex = ToolExecutor(registry=registry)
    res = ex.execute(tool_name="t1", arguments={"x": 1})

    _assert_contract(res, tool="t1")
    assert res["success"] is False
    assert res["result"] is None
    assert "boom" in (res["error"] or "")
    registry.get.assert_called_once_with("t1")
    tool.execute.assert_called_once_with(x=1)


def test_execute_json_invalid_json(tmp_path) -> None:
    _ = tmp_path
    registry = MagicMock(spec=ToolRegistry)
    ex = ToolExecutor(registry=registry)

    res = ex.execute_json("{invalid json")

    _assert_contract(res, tool=None)
    assert res["success"] is False
    assert res["result"] is None
    assert res["error"] is not None
