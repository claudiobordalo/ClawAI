from __future__ import annotations

from pathlib import Path

import pytest

from clawai.workspace.file_reader import FileReader
from clawai.workspace.ignore import IgnoreEngine, is_probably_binary
from clawai.workspace.project_tree import ProjectTree
from clawai.workspace.scanner import Scanner
from clawai.workspace.workspace import Workspace


def _write(path: Path, content: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def test_ignore_engine_internal_rules(tmp_path: Path) -> None:
    root = tmp_path

    (root / ".gitignore").write_text("ignored.txt\n!kept.txt\n", encoding="utf-8")

    ignore = IgnoreEngine(root)
    ignore.load()

    assert ignore.is_ignored(root / "node_modules" / "x.js", is_dir=True) is True
    assert ignore.is_ignored(root / ".venv" / "y", is_dir=True) is True
    assert ignore.is_ignored(root / "dist" / "a.js", is_dir=True) is True
    assert ignore.is_ignored(root / "build" / "b.js", is_dir=True) is True
    assert ignore.is_ignored(root / "__pycache__" / "z.pyc", is_dir=False) is True

    # .gitignore pattern without "/" matches basename
    assert ignore.is_ignored(root / "ignored.txt", is_dir=False) is True
    # ! negation
    assert ignore.is_ignored(root / "kept.txt", is_dir=False) is False


def test_ignore_engine_detects_binary(tmp_path: Path) -> None:
    root = tmp_path
    binary = root / "bin.dat"
    _write(binary, b"\x00\x01\x02\x03\x04")

    assert is_probably_binary(binary) is True

    reader = FileReader()
    assert reader.read_text(binary, max_chars=200) == ""


def test_scanner_lists_files_without_reading(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "a.py", "print('a')\n")
    _write(root / "node_modules" / "b.js", "print('b')\n")
    _write(root / "dist" / "c.js", "print('c')\n")
    (root / ".gitignore").write_text("", encoding="utf-8")

    ws = Workspace()
    ws.open_project(root)

    scanner = Scanner(root, ignore_engine=ws._ignore)  # type: ignore[attr-defined]
    files = scanner.list_files()

    rels = {str(p.relative_to(root)).replace("\\", "/") for p in files}
    assert "a.py" in rels
    assert "node_modules/b.js" not in rels
    assert "dist/c.js" not in rels


def test_project_tree_is_lightweight(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "agents" / "patch_agent.py", "print('x')\n")
    _write(root / "core" / "c1.py", "print('y')\n")
    _write(root / ".hidden" / "secret.py", "print('z')\n")
    (root / ".gitignore").write_text("", encoding="utf-8")

    ws = Workspace()
    ws.open_project(root)
    tree = ws.get_tree()

    assert isinstance(tree, ProjectTree)
    # deve excluir diretórios/pastas ocultas
    assert tree.root_node.name == root.name or tree.root_node.name == ""
    all_files = [n.name for n in tree.iter_files() if not n.is_dir]
    assert "patch_agent.py" in all_files
    assert "c1.py" in all_files
    assert "secret.py" not in all_files


def test_file_reader_read_text_respects_max_chars(tmp_path: Path) -> None:
    root = tmp_path
    f = root / "a.txt"
    _write(f, "a" * 5000)

    reader = FileReader()
    out = reader.read_text(f, max_chars=123)

    assert len(out) <= 123
    assert out == "a" * len(out)


def test_workspace_build_context_uses_scanner_and_reader(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "agents" / "patch_agent.py", "print('patch')\n")
    _write(root / "core" / "other.py", "print('core')\n")
    _write(root / "dist" / "ignored.js", "print('no')\n")
    (root / ".gitignore").write_text("", encoding="utf-8")

    ws = Workspace()
    context = ws.build_context(root, max_chars=200)

    # não deve incluir dist
    assert "ignored.js" not in context.replace("\\", "/")
    # deve incluir ao menos um bloco arquivável
    assert "agents/patch_agent.py" in context
