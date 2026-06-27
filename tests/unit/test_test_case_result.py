import pytest

from clawai.testing import TestCaseResult


def test_test_case_result_allowed_statuses_and_immutability():
    ok = TestCaseResult(name="t::a", status="passed", duration=0.0)
    assert ok.status == "passed"

    with pytest.raises(ValueError):
        TestCaseResult(name="t::b", status="unknown", duration=0.0)

    with pytest.raises(ValueError):
        TestCaseResult(name="t::c", status="failed", duration=-1.0)

    # dataclass is frozen
    with pytest.raises(Exception):
        ok.status = "failed"
