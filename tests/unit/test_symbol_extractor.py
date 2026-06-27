from __future__ import annotations

from pathlib import Path

from clawai.codebase import SymbolExtractor, ModuleInfo, ClassInfo, FunctionInfo


def write(tmp: Path, rel: str, content: str) -> Path:
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_symbol_extractor_empty_file(tmp_path: Path) -> None:
    p = write(tmp_path, "mod.py", "")
    ext = SymbolExtractor()
    m = ext.extract(p)
    assert isinstance(m, ModuleInfo)
    assert m.functions == ()
    assert m.classes == ()
    assert m.parse_error is None


def test_symbol_extractor_module_simple(tmp_path: Path) -> None:
    content = (
        '"""Module doc"""\n\n'
        'import os\n'
        'from . import sub\n\n'
        'x = 1\n\n'
        '@dec1\n'
        'def f1():\n'
        '    """Doc f1"""\n'
        '    pass\n\n'
        'class C:\n'
        '    """Doc C"""\n'
        '    @staticmethod\n'
        '    def m1():\n'
        '        """Doc m1"""\n'
        '        pass\n\n'
        'class D(C):\n'
        '    pass\n'
    )
    p = write(tmp_path, "mod.py", content)
    m = SymbolExtractor().extract(p)


    assert m.docstring == "Module doc"
    assert set(m.imports) == {"os", "."}

    # functions
    assert len(m.functions) == 1
    f = m.functions[0]
    assert isinstance(f, FunctionInfo)
    assert f.name == "f1"
    assert f.docstring == "Doc f1"
    assert "dec1" in f.decorators
    assert f.is_method is False

    # classes
    assert len(m.classes) == 2
    c = m.classes[0]
    assert isinstance(c, ClassInfo)
    assert c.name == "C"
    assert c.docstring == "Doc C"
    # methods
    assert len(c.methods) == 1
    m1 = c.methods[0]
    assert m1.is_method is True
    assert m1.name == "m1"

    d = m.classes[1]
    assert d.name == "D"
    assert d.bases == ("C",)


def test_symbol_extractor_decorators_and_imports(tmp_path: Path) -> None:
    content = (
        'from pkg.mod import name as alias\n\n'
        '@outer(inner=1)\n'
        'class X: ...\n\n'
        '@decorator\n'
        'async def g():\n'
        '    pass\n'
    )
    p = write(tmp_path, "a.py", content)
    m = SymbolExtractor().extract(p)

    assert "pkg.mod" in m.imports
    names = [fn.name for fn in m.functions]
    assert names == ["g"]
    assert any("decorator" in d for d in m.functions[0].decorators)
    assert any("outer" in d for d in m.classes[0].decorators)


def test_symbol_extractor_syntax_error(tmp_path: Path) -> None:
    content = (
        " def bad():\n"
        "    pass\n"
    )
    p = write(tmp_path, "bad.py", content)
    m = SymbolExtractor().extract(p)
    assert m.parse_error is not None
    assert m.functions == ()
    assert m.classes == ()
