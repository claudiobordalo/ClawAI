from __future__ import annotations

import pytest

from clawai.development import DevelopmentRequest


def test_development_request_creation_and_immutability(tmp_path):
    r = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="q", instructions="i")
    assert str(r.project_root) == str(tmp_path)
    assert r.objective == "obj"
    assert r.target_query == "q"
    assert r.instructions == "i"

    with pytest.raises(Exception):
        r.objective = "x"  # type: ignore[attr-defined]
