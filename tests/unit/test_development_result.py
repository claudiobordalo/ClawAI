from __future__ import annotations

import pytest

from clawai.development import DevelopmentResult
from clawai.diffing import Patch
from clawai.patching.patch_plan import PatchPlan
from clawai.planning.planner import ExecutionPlan, Planner
from clawai.verification.verification_result import VerificationResult


def test_development_result_success_and_error_and_immutability(tmp_path):
    exec_plan = Planner().create_plan("Do something")
    op_patch = Patch(file=str(tmp_path / "a.txt"), original="x", replacement="y", start_line=1, end_line=1, reason="r")
    patch_plan = PatchPlan.success_plan(operations=tuple(), summary="s")
    verification = VerificationResult.ok(checked_patches=1, passed=1, failed=0, warnings=tuple())

    ok = DevelopmentResult.ok(
        execution_plan=exec_plan,
        patch_plan=patch_plan,
        patches=(op_patch,),
        verification=verification,
        summary="done",
    )

    assert ok.success is True
    assert ok.execution_plan == exec_plan
    assert ok.patch_plan == patch_plan
    assert ok.patches == (op_patch,)
    assert ok.verification == verification
    assert ok.summary == "done"

    with pytest.raises(Exception):
        ok.summary = "x"  # type: ignore[attr-defined]

    err = DevelopmentResult.fail(summary="fail", error="e")
    assert err.success is False
    assert err.error == "e"
