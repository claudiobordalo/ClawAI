from __future__ import annotations

from pathlib import Path

from clawai.codebase import CodeAnalyzer
from clawai.retrieval import SymbolIndex, SymbolRef


def _build_proj(tmp: Path) -> Path:
    (tmp / "pkg").mkdir()
    (tmp / "pkg" / "__init__.py").write_text("")
    (tmp / "pkg" / "a.py").write_text(
        """
class A:
    def m(self):
        pass

def f():
    pass
        """
    )
    (tmp / "pkg" / "b.py").write_text("def g(): pass\n")
    return tmp


def test_symbol_index_basic_search(tmp_path: Path) -> None:
    root = _build_proj(tmp_path)
    snap = CodeAnalyzer().analyze(root)

    index = SymbolIndex(snap)

    # módulo
    mods = index.find_module("a")
    assert len(mods) == 1
    assert mods[0].kind == "module"
    assert mods[0].file.endswith("pkg/a.py")

    # classe
    classes = index.find_class("A")
    assert len(classes) == 1
    assert classes[0].kind == "class"
    assert classes[0].qualname == "A"

    # função
    fns = index.find_function("f")
    assert len(fns) == 1
    assert fns[0].kind == "function"

    # método via find_symbol
    syms = index.find_symbol("m")
    assert any(s.kind == "method" and s.qualname == "A.m" for s in syms)


def test_symbol_index_nonexistent_and_determinism(tmp_path: Path) -> None:
    root = _build_proj(tmp_path)
    snap = CodeAnalyzer().analyze(root)

    index = SymbolIndex(snap)
    none = index.find_function("zzz")
    assert none == ()

    # determinismo
    a1 = index.find_symbol("A")
    a2 = index.find_symbol("A")
    assert a1 == a2
