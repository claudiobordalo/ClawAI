import pytest

from clawai.executor import ExecutionResult
from clawai.selfrepair.repair_result import RepairResult
from clawai.selfrepair.repair_iteration import RepairIteration
from clawai.editor.edit_result import EditResult


def _rr(success=True):
    it = RepairIteration(iteration=1, development_result=None, test_result=None, diagnosis=None, success=success)
    return RepairResult(success=success, iterations=(it,), final_iteration=it, summary="s")


def test_execution_result_success_and_immutability(tmp_path):
    res = ExecutionResult(success=True, repair_result=_rr(True), applied_results=(EditResult.ok(file=tmp_path/"a", previous_content="", current_content=""),), summary="done")
    assert res.success is True and len(res.applied_results) == 1
    with pytest.raises(Exception):
        res.success = False


def test_execution_result_error():
    res = ExecutionResult(success=False, repair_result=_rr(False), applied_results=tuple(), summary="err", error="boom")
    assert res.error == "boom"
