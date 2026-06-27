import pytest

from clawai.testing import TestSuiteResult, TestCaseResult


def test_test_suite_result_invariants():
    r = TestSuiteResult(
        success=True,
        total=2,
        passed=2,
        failed=0,
        skipped=0,
        errors=0,
        duration=0.1,
        stdout="",
        stderr="",
        cases=(
            TestCaseResult(name="a::t1", status="passed", duration=0.01),
            TestCaseResult(name="a::t2", status="passed", duration=0.02),
        ),
    )
    assert r.total == 2
    assert r.success is True

    with pytest.raises(ValueError):
        TestSuiteResult(success=False, total=-1, passed=0, failed=0, skipped=0, errors=0, duration=0.0)

    with pytest.raises(ValueError):
        TestSuiteResult(success=False, total=1, passed=0, failed=0, skipped=0, errors=0, duration=-0.1)

    with pytest.raises(ValueError):
        # total mismatch
        TestSuiteResult(success=False, total=3, passed=1, failed=1, skipped=0, errors=0, duration=0.0)
