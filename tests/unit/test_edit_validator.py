from __future__ import annotations

from clawai.editor import EditOperation, EditValidator


def test_validator_file_does_not_exist(tmp_path):
    validator = EditValidator()
    missing = tmp_path / "missing.txt"
    op = EditOperation(file=missing, original_content="", new_content="new", reason="test")

    ok, error = validator.validate(op)
    assert ok is False
    assert error is not None and "exist" in error.lower()


def test_validator_original_content_differs(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("on-disk", encoding="utf-8")

    validator = EditValidator()
    op = EditOperation(file=f, original_content="different", new_content="new", reason="test")

    ok, error = validator.validate(op)
    assert ok is False
    assert error is not None and "original content" in error.lower()


def test_validator_new_content_identical(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("same", encoding="utf-8")

    validator = EditValidator()
    op = EditOperation(file=f, original_content="same", new_content="same", reason="test")

    ok, error = validator.validate(op)
    assert ok is False
    assert error is not None and "identical" in error.lower()


def test_validator_new_content_empty(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("content", encoding="utf-8")

    validator = EditValidator()
    op = EditOperation(file=f, original_content="content", new_content="", reason="test")

    ok, error = validator.validate(op)
    assert ok is False
    assert error is not None and "empty" in error.lower()


def test_validator_valid_operation(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("before", encoding="utf-8")

    validator = EditValidator()
    op = EditOperation(file=f, original_content="before", new_content="after", reason="test")

    ok, error = validator.validate(op)
    assert ok is True
    assert error is None
