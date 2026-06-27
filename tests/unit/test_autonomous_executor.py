import pytest

from clawai.executor import AutonomousExecutor, ExecutionRequest
from clawai.selfrepair.repair_result import RepairResult
from clawai.selfrepair.repair_iteration import RepairIteration
from clawai.development.development_result import DevelopmentResult
from clawai.patching.patch_plan import PatchPlan
from clawai.editor import EditOperation
from clawai.editor.edit_result import EditResult
from clawai.tracing.execution_trace import ExecutionTraceManager
from clawai.engineering import EngineeringMemory
from clawai.testing.test_diagnosis import DiagnosisResult


class FakeSelfRepair:
    def __init__(self, result: RepairResult):
        self._result = result
        self.calls = 0

    def run(self, req):  # noqa: D401
        self.calls += 1
        return self._result


class FakeEditor:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0
        self.applied_files = []

    def apply(self, operation: EditOperation):  # noqa: D401
        self.calls += 1
        self.applied_files.append(str(operation.file))
        out = self._outcomes[min(self.calls - 1, len(self._outcomes) - 1)]
        if isinstance(out, Exception):
            raise out
        return out


def _make_rr(success: bool, operations=()):
    it = RepairIteration(iteration=1, development_result=None, test_result=None, diagnosis=None, success=success)
    if success:
        dev = DevelopmentResult.ok(execution_plan=None, patch_plan=PatchPlan.success_plan(tuple(operations), summary="p"), patches=tuple(), verification=None, summary="ok")  # type: ignore[arg-type]
        it = RepairIteration(iteration=1, development_result=dev, test_result=None, diagnosis=None, success=True)
    return RepairResult(success=success, iterations=(it,), final_iteration=it, summary="s")


def _op(path: str, a: str, b: str) -> EditOperation:
    return EditOperation(file=path, original_content=a, new_content=b, reason="r")


def test_autonomous_selfrepair_fails_no_apply(tmp_path):
    rr = _make_rr(False)
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    res = ex.run(req)
    assert res.success is False and fake_ed.calls == 0


def test_autonomous_selfrepair_success_no_operations(tmp_path):
    rr = _make_rr(True, operations=())
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    res = ex.run(req)
    assert res.success is True and len(res.applied_results) == 0


def test_autonomous_one_operation_applied(tmp_path):
    ops = [_op("a.py", "x", "y")]
    rr = _make_rr(True, operations=ops)
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y")])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    res = ex.run(req)
    assert res.success is True and len(res.applied_results) == 1 and res.applied_results[0].success is True


def test_autonomous_multiple_operations_success(tmp_path):
    ops = [_op("a.py", "x", "y"), _op("b.py", "u", "v")]
    rr = _make_rr(True, operations=ops)
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([
        EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y"),
        EditResult.ok(file=tmp_path/"b.py", previous_content="u", current_content="v"),
    ])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    res = ex.run(req)
    assert res.success is True and len(res.applied_results) == 2 and all(r.success for r in res.applied_results)


def test_autonomous_fail_first_operation(tmp_path):
    ops = [_op("a.py", "x", "y"), _op("b.py", "u", "v")]
    rr = _make_rr(True, operations=ops)
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([
        EditResult.fail(file=tmp_path/"a.py", previous_content="x", current_content="x", error="validation failed"),
        EditResult.ok(file=tmp_path/"b.py", previous_content="u", current_content="v"),
    ])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    res = ex.run(req)
    assert res.success is False and len(res.applied_results) == 1 and fake_ed.calls == 1


def test_autonomous_fail_second_operation_interrupts(tmp_path):
    ops = [_op("a.py", "x", "y"), _op("b.py", "u", "v"), _op("c.py", "p", "q")]
    rr = _make_rr(True, operations=ops)
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([
        EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y"),
        EditResult.fail(file=tmp_path/"b.py", previous_content="u", current_content="u", error="apply error"),
        EditResult.ok(file=tmp_path/"c.py", previous_content="p", current_content="q"),
    ])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    res = ex.run(req)
    assert res.success is False and len(res.applied_results) == 2 and fake_ed.calls == 2


def test_autonomous_editor_exception(tmp_path):
    ops = [_op("a.py", "x", "y")]
    rr = _make_rr(True, operations=ops)
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([RuntimeError("editor boom")])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    res = ex.run(req)
    assert res.success is False and res.error is not None and len(res.applied_results) == 0


def test_autonomous_trace_integration(tmp_path):
    ops = [_op("a.py", "x", "y")]
    rr = _make_rr(True, operations=ops)
    trace = ExecutionTraceManager()
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y")])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed, trace=trace)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    _ = ex.run(req)
    events = trace.events()
    assert any(e.operation == "execution_started" for e in events)
    assert any(e.operation == "edit_applied" for e in events)
    assert any(e.operation == "execution_finished" for e in events)


def test_autonomous_determinism(tmp_path):
    ops = [_op("a.py", "x", "y")]
    rr = _make_rr(True, operations=ops)
    fake_sr = FakeSelfRepair(rr)
    fake_ed = FakeEditor([EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y")])
    ex = AutonomousExecutor(self_repair=fake_sr, editor=fake_ed)
    req = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    a = ex.run(req)
    b = ex.run(req)
    assert a == b


def _make_rr_with_diag(success: bool, operations=(), failing=("t::x",)):
    diag = DiagnosisResult(success=success, probable_causes=("cause",), failing_tests=tuple(failing), summary="diag summary")
    it = RepairIteration(iteration=1, development_result=None, test_result=None, diagnosis=diag, success=success)
    if success:
        dev = DevelopmentResult.ok(execution_plan=None, patch_plan=PatchPlan.success_plan(tuple(operations), summary="p"), patches=tuple(), verification=None, summary="ok")  # type: ignore[arg-type]
        it = RepairIteration(iteration=1, development_result=dev, test_result=None, diagnosis=diag, success=True)
    return RepairResult(success=success, iterations=(it,), final_iteration=it, summary="s")


def test_engineering_memory_saved_after_success(tmp_path):
    mem = EngineeringMemory()
    ops = [_op("a.py", "x", "y")]
    rr = _make_rr_with_diag(True, operations=ops, failing=tuple())
    ex = AutonomousExecutor(self_repair=FakeSelfRepair(rr), editor=FakeEditor([EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y")]), memory=mem)
    req = ExecutionRequest(project_root=tmp_path, objective="O", target_query="Q", instructions="I", max_iterations=1)
    res = ex.run(req)
    assert res.success is True
    assert mem.size() == 1
    rec = mem.last(1)[0]
    assert rec.objective == "O" and rec.target_query == "Q" and rec.instructions == "I"
    assert rec.success is True and rec.modified_files == ("a.py",) and rec.failed_tests == tuple()
    assert rec.strategy == "RepairStrategy" and rec.summary == rr.summary


def test_engineering_memory_saved_after_failure(tmp_path):
    mem = EngineeringMemory()
    rr = _make_rr_with_diag(False, operations=tuple(), failing=("t::a", "t::b"))
    ex = AutonomousExecutor(self_repair=FakeSelfRepair(rr), editor=FakeEditor([]), memory=mem)
    req = ExecutionRequest(project_root=tmp_path, objective="O", target_query="Q", instructions="I", max_iterations=1)
    res = ex.run(req)
    assert res.success is False
    assert mem.size() == 1
    rec = mem.last(1)[0]
    assert rec.success is False and rec.modified_files == tuple()
    assert rec.failed_tests == ("t::a", "t::b")


def test_engineering_memory_modified_files_and_strategy(tmp_path):
    mem = EngineeringMemory()
    ops = [_op("a.py", "x", "y"), _op("b.py", "u", "v")]
    rr = _make_rr_with_diag(True, operations=ops, failing=tuple())
    ex = AutonomousExecutor(
        self_repair=FakeSelfRepair(rr),
        editor=FakeEditor([
            EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y"),
            EditResult.ok(file=tmp_path/"b.py", previous_content="u", current_content="v"),
        ]),
        memory=mem,
    )
    req = ExecutionRequest(project_root=tmp_path, objective="O", target_query="Q", instructions="I", max_iterations=1)
    _ = ex.run(req)
    rec = mem.last(1)[0]
    assert rec.modified_files == ("a.py", "b.py")
    assert rec.strategy == "RepairStrategy"


def test_engineering_memory_no_disk_write(tmp_path):
    mem = EngineeringMemory()
    rr = _make_rr_with_diag(True, operations=(_op("a.py", "x", "y"),), failing=tuple())
    ed = FakeEditor([EditResult.ok(file=tmp_path/"a.py", previous_content="x", current_content="y")])
    ex = AutonomousExecutor(self_repair=FakeSelfRepair(rr), editor=ed, memory=mem)
    req = ExecutionRequest(project_root=tmp_path, objective="O", target_query="Q", instructions="I", max_iterations=1)
    _ = ex.run(req)
    # Ensure editor was called but no actual file IO is required for this test
    assert ed.calls == 1 and mem.size() == 1
