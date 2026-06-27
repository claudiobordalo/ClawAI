from __future__ import annotations

import pytest

from clawai.patching import ChangeRequest


def test_change_request_creation():
    cr = ChangeRequest(objective="Improve code", target_query="editor", instructions="Refactor module")
    assert cr.objective == "Improve code"
    assert cr.target_query == "editor"
    assert cr.instructions == "Refactor module"


def test_change_request_immutable():
    cr = ChangeRequest(objective="A", target_query="B", instructions="C")
    with pytest.raises(Exception):
        cr.objective = "X"  # type: ignore[attr-defined]
