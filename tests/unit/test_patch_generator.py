from __future__ import annotations

from clawai.diffing import PatchGenerator
from clawai.editor import EditOperation


def make_op(s1: str, s2: str, file: str = "a.txt") -> EditOperation:
    return EditOperation(file=file, original_content=s1, new_content=s2, reason="change")


def test_patch_generator_single_line_change():
    op = make_op("a\nb\nc", "a\nB\nc")
    gen = PatchGenerator()
    res = gen.generate(op)

    assert res.success is True
    assert len(res.patches) == 1
    p = res.patches[0]
    assert p.start_line == 2 and p.end_line == 2
    assert p.original == "b" and p.replacement == "B"


def test_patch_generator_multi_lines_replace():
    op = make_op("a\nb\nc\nd", "a\nX\nY\nd")
    gen = PatchGenerator()
    res = gen.generate(op)

    assert res.success is True
    assert len(res.patches) == 1
    p = res.patches[0]
    assert p.start_line == 2 and p.end_line == 3
    assert p.original == "b\nc" and p.replacement == "X\nY"


def test_patch_generator_insertion():
    op = make_op("a\nc", "a\nb\nc")
    gen = PatchGenerator()
    res = gen.generate(op)

    assert res.success is True
    assert len(res.patches) == 1
    p = res.patches[0]
    # Insertion represented as empty original with insertion before start_line
    assert p.original == "" and p.replacement == "b"
    assert p.start_line == 2 and p.end_line == 1


def test_patch_generator_removal():
    op = make_op("a\nb\nc", "a\nc")
    gen = PatchGenerator()
    res = gen.generate(op)

    assert res.success is True
    assert len(res.patches) == 1
    p = res.patches[0]
    assert p.start_line == 2 and p.end_line == 2
    assert p.original == "b" and p.replacement == ""


def test_patch_generator_no_changes():
    op = make_op("same", "same")
    gen = PatchGenerator()
    res = gen.generate(op)

    assert res.success is False


def test_patch_generator_determinism():
    op = make_op("a\nb\nc\nd", "A\nb\nc\nD")
    gen = PatchGenerator()
    r1 = gen.generate(op)
    r2 = gen.generate(op)

    assert r1 == r2
    assert r1.success is True
    # Two separate replacements should yield two patches
    assert len(r1.patches) == 2
