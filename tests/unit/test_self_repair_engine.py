import sys
from pathlib import Path

import pytest

from clawai.selfrepair import SelfRepairEngine, RepairRequest
from clawai.development.development_result import DevelopmentResult
from clawai.testing import TestSuiteResult, TestCaseResult
from clawai.testing.test_diagnosis import DiagnosisResult
from clawai.tracing.execution_trace import ExecutionTraceManager


class FakePipeline:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0
        self.received_instructions = []

    def run(self, req):  # noqa: D401
        self.calls += 1
        # record instructions used
        self.received_instructions.append(getattr(req, "instructions", None))
        out = self._outcomes[min(self.calls - 1, len(self._outcomes) - 1)]
        if isinstance(out, Exception):
            raise out
        return out


class FakeRunner:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0

    def run(self, test_request):  # noqa: D401
        self.calls += 1
        out = self._outcomes[min(self.calls - 1, len(self._outcomes) - 1)]
        if isinstance(out, Exception):
            raise out
        return out


class FakeDiagnosis:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0

    def diagnose(self, suite):  # noqa: D401
        self.calls += 1
        out = self._outcomes[min(self.calls - 1, len(self._outcomes) - 1)]
        if isinstance(out, Exception):
            raise out
        return out


def _dev_ok():
    return DevelopmentResult.ok(
        execution_plan=None,  # type: ignore[arg-type]
        patch_plan=None,      # type: ignore[arg-type]
        patches=tuple(),
        verification=None,    # type: ignore[arg-type]
        summary="ok",
    )


def _ts_ok():
    return TestSuiteResult(success=True, total=1, passed=1, failed=0, skipped=0, errors=0, duration=0.0, stdout="", stderr="", cases=(TestCaseResult(name="t::a", status="passed", duration=0.0),))


def _ts_fail():
    return TestSuiteResult(success=False, total=1, passed=0, failed=1, skipped=0, errors=0, duration=0.0, stdout="", stderr="E AssertionError", cases=(TestCaseResult(name="t::a", status="failed", duration=0.0, message="assert 1 == 2"),))


def _diag_ok():
    return DiagnosisResult(success=True, probable_causes=tuple(), failing_tests=tuple(), summary="ok")


def _diag_fail():
    return DiagnosisResult(success=False, probable_causes=("assertion failure",), failing_tests=("t::a",), summary="fail")


def _make_engine(pipeline, runner, diag, trace=None):
    return SelfRepairEngine(pipeline=pipeline, test_runner=runner, diagnosis=diag, trace=trace)


def test_self_repair_success_first_iteration(tmp_path: Path):
    eng = _make_engine(FakePipeline([_dev_ok()]), FakeRunner([_ts_ok()]), FakeDiagnosis([_diag_ok()]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=3)
    res = eng.run(req)
    assert res.success is True
    assert len(res.iterations) == 1


def test_self_repair_success_second_iteration(tmp_path: Path):
    eng = _make_engine(FakePipeline([_dev_ok(), _dev_ok()]), FakeRunner([_ts_fail(), _ts_ok()]), FakeDiagnosis([_diag_fail(), _diag_ok()]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=3)
    res = eng.run(req)
    assert res.success is True
    assert len(res.iterations) == 2


def test_self_repair_fails_until_max_iterations(tmp_path: Path):
    eng = _make_engine(FakePipeline([_dev_ok(), _dev_ok()]), FakeRunner([_ts_fail(), _ts_fail()]), FakeDiagnosis([_diag_fail(), _diag_fail()]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=2)
    res = eng.run(req)
    assert res.success is False
    assert len(res.iterations) == 2
    assert res.final_iteration is res.iterations[-1]


def test_self_repair_pipeline_exception(tmp_path: Path):
    eng = _make_engine(FakePipeline([RuntimeError("pipeline boom")]), FakeRunner([_ts_ok()]), FakeDiagnosis([_diag_ok()]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=2)
    res = eng.run(req)
    assert res.success is False and res.error is not None
    assert len(res.iterations) == 1


def test_self_repair_test_runner_exception(tmp_path: Path):
    eng = _make_engine(FakePipeline([_dev_ok()]), FakeRunner([RuntimeError("runner boom")]), FakeDiagnosis([_diag_ok()]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=2)
    res = eng.run(req)
    assert res.success is False and res.error is not None
    assert len(res.iterations) == 1


def test_self_repair_diagnosis_exception(tmp_path: Path):
    eng = _make_engine(FakePipeline([_dev_ok()]), FakeRunner([_ts_ok()]), FakeDiagnosis([RuntimeError("diag boom")]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=2)
    res = eng.run(req)
    assert res.success is False and res.error is not None
    assert len(res.iterations) == 1


def test_self_repair_trace_integration(tmp_path: Path):
    trace = ExecutionTraceManager()
    eng = _make_engine(FakePipeline([_dev_ok()]), FakeRunner([_ts_ok()]), FakeDiagnosis([_diag_ok()]), trace=trace)
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=3)
    res = eng.run(req)
    events = trace.events()
    assert any(e.operation == "repair_iteration_started" for e in events)
    assert any(e.operation == "development_completed" for e in events)
    assert any(e.operation == "tests_completed" for e in events)
    assert any(e.operation == "diagnosis_completed" for e in events)
    assert any(e.operation == "repair_finished" for e in events)


def test_self_repair_no_disk_writes(tmp_path: Path):
    # Execution should not create files in project root
    pre = set(p.name for p in tmp_path.iterdir())
    eng = _make_engine(FakePipeline([_dev_ok()]), FakeRunner([_ts_ok()]), FakeDiagnosis([_diag_ok()]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    _ = eng.run(req)
    post = set(p.name for p in tmp_path.iterdir())
    assert post == pre


def test_self_repair_determinism(tmp_path: Path):
    eng = _make_engine(FakePipeline([_dev_ok()]), FakeRunner([_ts_ok()]), FakeDiagnosis([_diag_ok()]))
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=1)
    a = eng.run(req)
    b = eng.run(req)
    assert a == b


def test_strategy_integration_updates_instructions(tmp_path: Path):
    # Three iterations: fail, fail, pass with changing diagnosis summaries/causes
    p = FakePipeline([_dev_ok(), _dev_ok(), _dev_ok()])
    r = FakeRunner([_ts_fail(), _ts_fail(), _ts_ok()])
    d1 = DiagnosisResult(success=False, probable_causes=("ModuleNotFoundError",), failing_tests=("t::a",), summary="missing module")
    d2 = DiagnosisResult(success=False, probable_causes=("AssertionError",), failing_tests=("t::a",), summary="assert failed")
    d3 = DiagnosisResult(success=True, probable_causes=tuple(), failing_tests=tuple(), summary="ok")
    diag = FakeDiagnosis([d1, d2, d3])

    eng = _make_engine(p, r, diag)
    req = RepairRequest(project_root=tmp_path, objective="o", target_query="q", instructions="base instruction", max_iterations=3)
    _ = eng.run(req)

    # First iteration uses original instruction
    assert p.received_instructions[0] == "base instruction"
    # Second iteration uses strategy output including objective and previous summary/causes
    assert p.received_instructions[1] != "base instruction"
    assert "Objective:" in p.received_instructions[1]
    assert "missing module" in p.received_instructions[1]
    assert "ModuleNotFoundError" in p.received_instructions[1]
    # Third iteration uses updated diagnosis summary/causes
    assert "assert failed" in p.received_instructions[2]
    assert "AssertionError" in p.received_instructions[2]
