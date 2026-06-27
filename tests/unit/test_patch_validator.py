from __future__ import annotations

import pytest

from clawai.diffing import Patch, PatchValidator
from clawai.diffing.patch_generator import PatchGenerator
from clawai.editor import EditOperation


def test_patch_validator_valid_patch(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc", encoding="utf-8")

    patch = Patch(file=str(f), original="b", replacement="B", start_line=2, end_line=2, reason="r")

    validator = PatchValidator()
    ok, err = validator.validate(patch)
    assert ok is True and err is None


def test_patch_validator_invalid_lines(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc", encoding="utf-8")

    p1 = Patch(file=str(f), original="b", replacement="B", start_line=0, end_line=0, reason="r")
    ok, _ = PatchValidator().validate(p1)
    assert ok is False

    # Insertion with wrong end_line
    p2 = Patch(file=str(f), original="", replacement="X", start_line=2, end_line=2, reason="r")
    ok, _ = PatchValidator().validate(p2)
    assert ok is False


def test_patch_validator_replacement_equal(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc", encoding="utf-8")

    p = Patch(file=str(f), original="b", replacement="b", start_line=2, end_line=2, reason="r")
    ok, err = PatchValidator().validate(p)
    assert ok is False and "idêntico" in (err or "").lower()


def test_patch_validator_empty_content(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc", encoding="utf-8")

    p = Patch(file=str(f), original="", replacement="", start_line=2, end_line=1, reason="r")
    ok, err = PatchValidator().validate(p)
    assert ok is False and "vazio" in (err or "").lower()


def test_patch_validator_integration_with_generator(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc\nd", encoding="utf-8")

    op = EditOperation(file=str(f), original_content="a\nb\nc\nd", new_content="A\nb\nC\nd", reason="update")
    gen = PatchGenerator()
    res = gen.generate(op)

    assert res.success is True

    validator = PatchValidator()
    for p in res.patches:
        ok, err = validator.validate(p)
        assert ok is True and err is None
