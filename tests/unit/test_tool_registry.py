from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from clawai.tools.filesystem_tool import FilesystemTool
from clawai.tools.tool_registry import ToolRegistry
from clawai.tools.tool import Tool


class DummyTool(Tool):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "dummy"

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {"echo": kwargs}

    def health(self) -> dict[str, Any]:
        return {"ok": True}

    def describe(self) -> ToolDescriptor:
        from clawai.tools.tool_descriptor import ToolDescriptor
        return ToolDescriptor(name=self._name, description="dummy")


def _assert_contract(res: dict[str, Any]) -> None:
    assert set(res.keys()) == {"success", "result", "error", "duration_ms"}
    assert isinstance(res["success"], bool)
    assert res["duration_ms"] >= 0
    assert res["error"] is None or isinstance(res["error"], str)


def test_register_unregister_get_list_health(tmp_path: Path) -> None:
    _ = tmp_path  # tmp_path used to satisfy constraint (no real FS access)

    registry = ToolRegistry()

    res = registry.health()
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"]["registered_tools"] == 0

    t1 = DummyTool("t1")
    res = registry.register(t1)
    _assert_contract(res)
    assert res["success"] is True
    assert registry.list_tools()["result"]  # list_tools also contract-tested below

    res = registry.get("t1")
    _assert_contract(res)
    assert res["success"] is True
    assert isinstance(res["result"], Tool)

    res = registry.list_tools()
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"] == ["t1"]

    res = registry.unregister("t1")
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"]["existed"] is True

    res = registry.get("t1")
    _assert_contract(res)
    assert res["success"] is False

    res = registry.unregister("missing")
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"]["existed"] is False


def test_list_tools_empty(tmp_path: Path) -> None:
    _ = tmp_path
    registry = ToolRegistry()
    res = registry.list_tools()
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"] == []
