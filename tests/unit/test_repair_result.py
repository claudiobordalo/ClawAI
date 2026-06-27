import pytest

from clawai.selfrepair import RepairResult, RepairIteration


def test_repair_result_success_and_immutability():
    it = RepairIteration(iteration=1, development_result=None, test_result=None, diagnosis=None, success=True)
    r = RepairResult(success=True, iterations=(it,), final_iteration=it, summary="done")
    assert r.success is True and r.final_iteration is it
    with pytest.raises(Exception):
        r.success = False


def test_repair_result_error():
    it = RepairIteration(iteration=1, development_result=None, test_result=None, diagnosis=None, success=False)
    r = RepairResult(success=False, iterations=(it,), final_iteration=it, summary="err", error="boom")
    assert r.error == "boom"
