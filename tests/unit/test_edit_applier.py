from __future__ import annotations

import builtins

import pytest

from clawai.editor import EditApplier, EditOperation


def test_edit_applier_success(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("old", encoding="utf-8")

    op = EditOperation(file=f, original_content="old", new_content="new", reason="update")

    applier = EditApplier()
    result = applier.apply(op)

    assert result.success is True
    assert result.previous_content == "old"
    assert (tmp_path / "file.txt").read_text(encoding="utf-8") == "new"
    assert result.current_content == "new"
    assert result.error is None


def test_edit_applier_write_failure(monkeypatch, tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("keep", encoding="utf-8")

    real_open = builtins.open

    def failing_open(path, mode="r", *args, **kwargs):  # pragma: no cover - exercised in failure path
        if "w" in mode:
            raise OSError("simulated write failure")
        return real_open(path, mode, *args, **kwargs)

    # Patch only the applier's module open so other I/O remains normal
    import clawai.editor.edit_applier as applier_module

    monkeypatch.setattr(applier_module, "open", failing_open, raising=False)

    applier = EditApplier()
    op = EditOperation(file=f, original_content="keep", new_content="new", reason="update")

    result = applier.apply(op)

    assert result.success is False
    assert result.previous_content == "keep"
    assert result.error is not None and "write" in result.error.lower()
    # Content on disk must remain unchanged on write failure
    assert f.read_text(encoding="utf-8") == "keep"


def test_edit_applier_deterministic_failure(monkeypatch, tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("data", encoding="utf-8")

    real_open = builtins.open

    def failing_open(path, mode="r", *args, **kwargs):  # pragma: no cover
        if "w" in mode:
            raise OSError("simulated write failure")
        return real_open(path, mode, *args, **kwargs)

    import clawai.editor.edit_applier as applier_module

    monkeypatch.setattr(applier_module, "open", failing_open, raising=False)

    applier = EditApplier()
    op = EditOperation(file=f, original_content="data", new_content="other", reason="update")

    r1 = applier.apply(op)
    r2 = applier.apply(op)

    assert r1 == r2
    assert r1.success is False
