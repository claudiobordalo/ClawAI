from __future__ import annotations

from pathlib import Path

from clawai.codebase import CodeAnalyzer, ProjectSnapshot


def test_code_analyzer_empty_project(tmp_path: Path) -> None:
    analyzer = CodeAnalyzer()
    snap = analyzer.analyze(tmp_path)

    assert isinstance(snap, ProjectSnapshot)
    assert snap.files == ()
    assert snap.modules == ()


def test_code_analyzer_simple_project(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def x(): pass\n")
    (tmp_path / "readme.md").write_text("# readme\n")

    analyzer = CodeAnalyzer()
    snap = analyzer.analyze(tmp_path)

    assert any(f.path.endswith("a.py") for f in snap.files)
    assert any(f.path.endswith("readme.md") for f in snap.files)

    # Modules only for .py
    assert len(snap.modules) == 1
    assert snap.modules[0].functions[0].name == "x"


def test_code_analyzer_multi_module_and_graph(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "a.py").write_text("from . import b\nclass A: pass\n")
    (tmp_path / "pkg" / "b.py").write_text("def f(): pass\n")

    analyzer = CodeAnalyzer()
    snap1 = analyzer.analyze(tmp_path)
    snap2 = analyzer.analyze(tmp_path)

    assert len(snap1.modules) == 2
    assert snap1.dependency_graph is not None

    # Determinism
    assert snap1 == snap2
