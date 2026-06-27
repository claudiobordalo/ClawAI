import pytest

from clawai.selfrepair import RepairIteration
from clawai.development.development_result import DevelopmentResult
from clawai.testing import TestSuiteResult, TestCaseResult
from clawai.testing.test_diagnosis import DiagnosisResult


def _dev_ok():
    return DevelopmentResult.ok(
        execution_plan=None,  # type: ignore[arg-type]
        patch_plan=None,      # type: ignore[arg-type]
        patches=tuple(),
        verification=None,    # type: ignore[arg-type]
        summary="ok",
    )


def _ts_ok():
    return TestSuiteResult(success=True, total=1, passed=1, failed=0, skipped=0, errors=0, duration=0.1, stdout="", stderr="", cases=(TestCaseResult(name="t::a", status="passed", duration=0.0),))


def _diag_ok():
    return DiagnosisResult(success=True, probable_causes=tuple(), failing_tests=tuple(), summary="ok")


def test_repair_iteration_creation_and_immutability():
    it = RepairIteration(iteration=1, development_result=_dev_ok(), test_result=_ts_ok(), diagnosis=_diag_ok(), success=True)
    assert it.iteration == 1 and it.success is True
    with pytest.raises(Exception):
        it.success = False
