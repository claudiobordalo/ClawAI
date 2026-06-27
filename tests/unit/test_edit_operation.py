from __future__ import annotations

import pytest

from clawai.editor import EditOperation


def test_edit_operation_is_immutable():
    op = EditOperation(file="some.txt", original_content="a", new_content="b", reason="test")
    with pytest.raises(Exception):
        # Dataclasses with frozen=True raise FrozenInstanceError (a subclass of AttributeError)
        op.new_content = "c"  # type: ignore[attr-defined]


def test_edit_operation_fields_and_path(tmp_path):
    f = tmp_path / "file.txt"
    op = EditOperation(file=f, original_content="x", new_content="y", reason="because")

    assert op.file == f
    assert op.original_content == "x"
    assert op.new_content == "y"
    assert op.reason == "because"
    assert op.file_path() == f
