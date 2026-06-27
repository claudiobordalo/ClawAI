from __future__ import annotations

import pytest

from clawai.editor import EditOperation
from clawai.patching import PatchPlan


def test_patch_plan_success_and_immutability(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("OLD", encoding="utf-8")

    op = EditOperation(file=str(f), original_content="OLD", new_content="NEW", reason="update")
    plan = PatchPlan.success_plan((op,), summary="One change")

    assert plan.success is True
    assert plan.summary == "One change"
    assert plan.error is None
    assert plan.operations == (op,)

    with pytest.raises(Exception):
        plan.summary = "other"  # type: ignore[attr-defined]


def test_patch_plan_error():
    plan = PatchPlan.error_plan("Something went wrong")
    assert plan.success is False
    assert plan.error == "Something went wrong"
    assert plan.operations == tuple()
