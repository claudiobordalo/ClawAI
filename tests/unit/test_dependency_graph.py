from __future__ import annotations

from pathlib import Path

from clawai.codebase import SymbolExtractor, DependencyGraph


def test_dependency_graph_single_module(tmp_path: Path) -> None:
    p = tmp_path / "m.py"
    p.write_text("def a(): pass\nclass C: pass\n")
    mod = SymbolExtractor().extract(p)

    graph = DependencyGraph.build((mod,))
    assert len(graph.modules) == 1
    node = graph.modules[0]
    assert node.file.endswith("m.py")
    assert set(node.defined_symbols) == {"a", "C"}
    assert node.imports == ()


def test_dependency_graph_multiple_and_imports(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "a.py").write_text("import os\nfrom . import b\nclass A: pass\n")
    (tmp_path / "pkg" / "b.py").write_text("def f(): pass\n")

    ext = SymbolExtractor()
    m1 = ext.extract(tmp_path / "pkg" / "a.py")
    m2 = ext.extract(tmp_path / "pkg" / "b.py")

    graph = DependencyGraph.build((m1, m2))
    assert len(graph.modules) == 2

    files = [n.file for n in graph.modules]
    assert any(f.endswith("a.py") for f in files)
    assert any(f.endswith("b.py") for f in files)

    # imports
    a_node = next(n for n in graph.modules if n.file.endswith("a.py"))
    assert set(a_node.imports) == {"os", "."}

    # stability
    graph2 = DependencyGraph.build((m1, m2))
    assert graph == graph2
