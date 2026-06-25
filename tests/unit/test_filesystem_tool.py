from __future__ import annotations

from pathlib import Path

import pytest

from clawai.tools.filesystem_tool import FilesystemTool
from clawai.workspace.ignore import IgnoreEngine


def _assert_contract(res: dict) -> None:
    assert set(res.keys()) == {"success", "result", "error", "duration_ms"}
    assert isinstance(res["success"], bool)
    assert res["duration_ms"] >= 0
    assert res["error"] is None or isinstance(res["error"], str)


def test_health(tmp_path: Path) -> None:
    tool = FilesystemTool()
    res = tool.health()
    _assert_contract(res)
    assert res["success"] is True


def test_write_read_append_delete_exists_mkdir_list_dir(tmp_path: Path) -> None:
    tool = FilesystemTool()

    p = tmp_path / "a" / "b" / "file.txt"

    # mkdir
    res = tool.mkdir(str(p.parent))
    _assert_contract(res)
    assert res["success"] is True

    # exists (not yet)
    res = tool.exists(str(p))
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"] is False

    # write
    res = tool.write_file(str(p), "hello")
    _assert_contract(res)
    assert res["success"] is True

    # exists
    res = tool.exists(str(p))
    _assert_contract(res)
    assert res["result"] is True

    # read
    res = tool.read_file(str(p))
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"] == b"hello"

    # append
    res = tool.append_file(str(p), " world")
    _assert_contract(res)
    assert res["success"] is True

    # read_text
    res = tool.read_text(str(p))
    _assert_contract(res)
    assert res["success"] is True
    assert res["result"] == "hello world"

    # list_dir
    res = tool.list_dir(str(p.parent))
    _assert_contract(res)
    assert res["success"] is True
    assert any(Path(x).name == "file.txt" for x in res["result"])

    # delete
    res = tool.delete_file(str(p))
    _assert_contract(res)
    assert res["success"] is True

    # delete non-existing should fail
    res = tool.delete_file(str(p))
    _assert_contract(res)
    assert res["success"] is False


def test_read_nonexistent(tmp_path: Path) -> None:
    tool = FilesystemTool()
    res = tool.read_text(str(tmp_path / "nope.txt"))
    _assert_contract(res)
    assert res["success"] is False


def test_copy_move(tmp_path: Path) -> None:
    tool = FilesystemTool()

    src = tmp_path / "src.txt"
    dst = tmp_path / "dst" / "dst.txt"
    moved = tmp_path / "moved.txt"

    src.write_text("x", encoding="utf-8")

    res = tool.copy(str(src), str(dst))
    _assert_contract(res)
    assert res["success"] is True
    assert dst.exists()

    res = tool.move(str(dst), str(moved))
    _assert_contract(res)
    assert res["success"] is True
    assert moved.exists()
    assert not dst.exists()


def test_search_uses_rglob_and_ignore_engine(tmp_path: Path) -> None:
    # root dir layout
    root = tmp_path
    keep_dir = root / "keep"
    ignore_dir = root / "node_modules"
    keep_dir.mkdir()
    ignore_dir.mkdir()

    (keep_dir / "a.txt").write_text("a", encoding="utf-8")
    (ignore_dir / "b.txt").write_text("b", encoding="utf-8")

    # Also create .gitignore to ignore a specific glob
    # (use a pattern compatible with the IgnoreEngine subset implementation)
    (root / ".gitignore").write_text("ignored/*.txt\n", encoding="utf-8")
    (root / "ignored").mkdir()
    (root / "ignored" / "c.txt").write_text("c", encoding="utf-8")

    ig = IgnoreEngine(root)
    ig.load()

    tool = FilesystemTool(ignore_engine=ig)
    res = tool.search(str(root), "*.txt")
    _assert_contract(res)
    assert res["success"] is True

    found = {Path(p).name for p in res["result"]}
    assert "a.txt" in found
    assert "b.txt" not in found  # node_modules ignored by internal rules
    assert "c.txt" not in found  # via .gitignore
