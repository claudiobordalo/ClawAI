from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from clawai.development import DevelopmentPipeline, DevelopmentRequest
from clawai.diffing import PatchGenerator
from clawai.patching import ChangeRequest, PatchPlanner
from clawai.patching.patch_plan import PatchPlan
from clawai.planning.planner import ExecutionPlan, Planner
from clawai.tracing.execution_trace import ExecutionTraceManager
from clawai.verification import SelfVerifier, RuleEngine
from clawai.diffing.patch_validator import PatchValidator


# Fakes determinísticos
@dataclass(frozen=True)
class PlanningResultFake:
    success: bool
    plan: ExecutionPlan | None
    error: str | None = None


class FakeLLMPlanner:
    def __init__(self, ok: bool = True):
        self._ok = ok

    def create_plan(self, objective: str) -> PlanningResultFake:
        if not self._ok:
            return PlanningResultFake(False, None, "llm fail")
        plan = Planner().create_plan(objective, steps=("step1",))
        return PlanningResultFake(True, plan)


class FakeAnalyzer:
    def __init__(self, files: tuple[str, ...], fail: bool = False):
        self._files = files
        self._fail = fail

    def analyze(self, root):
        if self._fail:
            raise RuntimeError("analyze fail")
        from clawai.codebase.project_snapshot import ProjectSnapshot, SourceFile
        abs_files = tuple(str(Path(root) / f) for f in self._files)
        sf = tuple(SourceFile(path=f, extension=Path(f).suffix) for f in abs_files)
        return ProjectSnapshot(root=str(Path(root)), files=sf)


@dataclass(frozen=True)
class FakeRetrieval:
    files: tuple[str, ...]


class FakeRetriever:
    def __init__(self, files: tuple[str, ...]):
        self._files = files

    def retrieve(self, snapshot, query):
        return FakeRetrieval(files=self._files)


class FakePatchPlanner(PatchPlanner):
    def __init__(self, plan: PatchPlan):
        # bypass super init
        self._plan = plan

    def plan(self, request: ChangeRequest, project_root):
        return self._plan


class FailingPatchGenerator(PatchGenerator):
    def generate(self, operation):  # type: ignore[override]
        from clawai.diffing.patch_result import PatchResult
        return PatchResult.fail("gen fail")


class FailingSelfVerifier(SelfVerifier):
    def __init__(self):
        pass

    def verify(self, patches):  # type: ignore[override]
        from clawai.verification.verification_result import VerificationResult
        return VerificationResult.fail(checked_patches=len(tuple(patches)), passed=0, failed=1, warnings=tuple(), errors=("verify fail",))


def make_ok_pipeline(tmp_path):
    # Prepare file
    f = tmp_path / "a.txt"
    f.write_text("A", encoding="utf-8")

    # PatchPlanner returns one operation updating file a.txt from A to B
    from clawai.editor import EditOperation
    op = EditOperation(file=str(f), original_content="A", new_content="B", reason="r")
    patch_plan = PatchPlan.success_plan((op,), summary="one change")

    pipeline = DevelopmentPipeline(
        llm_planner=FakeLLMPlanner(),
        code_analyzer=FakeAnalyzer(files=("a.txt",)),
        context_retriever=FakeRetriever(files=("a.txt",)),
        patch_planner=FakePatchPlanner(patch_plan),
        patch_generator=PatchGenerator(),
        self_verifier=SelfVerifier(patch_validator=PatchValidator(), rule_engine=RuleEngine(SelfVerifier.default_rules())),
        trace=ExecutionTraceManager(),
    )
    return pipeline, f


def test_development_pipeline_full_flow_and_trace_and_no_disk_write(tmp_path):
    pipeline, f = make_ok_pipeline(tmp_path)

    req = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="a.txt", instructions="i")
    res = pipeline.run(req)

    assert res.success is True
    assert res.execution_plan is not None
    assert res.patch_plan is not None
    assert len(res.patches) >= 1
    assert res.verification is not None and res.verification.success is True

    # No writes to disk
    assert f.read_text(encoding="utf-8") == "A"

    # Trace captured
    assert pipeline._trace.size() >= 6  # plan, analyze, retrieve, patch_plan, generate_patches, verify_patches


def test_development_pipeline_fail_llm_planner(tmp_path):
    pipeline, f = make_ok_pipeline(tmp_path)
    pipeline = DevelopmentPipeline(
        llm_planner=FakeLLMPlanner(ok=False),
        code_analyzer=pipeline._analyzer,
        context_retriever=pipeline._retriever,
        patch_planner=pipeline._patch_planner,
        patch_generator=pipeline._patch_generator,
        self_verifier=pipeline._self_verifier,
        trace=ExecutionTraceManager(),
    )

    req = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="a.txt", instructions="i")
    res = pipeline.run(req)

    assert res.success is False
    assert "planning" in (res.summary or "").lower()


def test_development_pipeline_fail_code_analyzer(tmp_path):
    pipeline, f = make_ok_pipeline(tmp_path)
    bad_analyzer = FakeAnalyzer(files=tuple(), fail=True)
    pipeline = DevelopmentPipeline(
        llm_planner=pipeline._llm_planner,
        code_analyzer=bad_analyzer,
        context_retriever=pipeline._retriever,
        patch_planner=pipeline._patch_planner,
        patch_generator=pipeline._patch_generator,
        self_verifier=pipeline._self_verifier,
        trace=ExecutionTraceManager(),
    )

    req = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="a.txt", instructions="i")
    res = pipeline.run(req)

    assert res.success is False
    assert "pipeline error" in (res.summary or "").lower()


def test_development_pipeline_fail_patch_planner(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("A", encoding="utf-8")

    bad_plan = PatchPlan.error_plan("nope")

    pipeline = DevelopmentPipeline(
        llm_planner=FakeLLMPlanner(),
        code_analyzer=FakeAnalyzer(files=("a.txt",)),
        context_retriever=FakeRetriever(files=("a.txt",)),
        patch_planner=FakePatchPlanner(bad_plan),
        patch_generator=PatchGenerator(),
        self_verifier=SelfVerifier(patch_validator=PatchValidator(), rule_engine=RuleEngine(SelfVerifier.default_rules())),
        trace=ExecutionTraceManager(),
    )

    req = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="a.txt", instructions="i")
    res = pipeline.run(req)

    assert res.success is False
    assert "patch planning" in (res.summary or "").lower()


def test_development_pipeline_fail_patch_generator(tmp_path):
    pipeline, f = make_ok_pipeline(tmp_path)

    pipeline = DevelopmentPipeline(
        llm_planner=pipeline._llm_planner,
        code_analyzer=pipeline._analyzer,
        context_retriever=pipeline._retriever,
        patch_planner=pipeline._patch_planner,
        patch_generator=FailingPatchGenerator(),
        self_verifier=pipeline._self_verifier,
        trace=ExecutionTraceManager(),
    )

    req = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="a.txt", instructions="i")
    res = pipeline.run(req)

    assert res.success is False
    assert "patch generation" in (res.summary or "").lower()


def test_development_pipeline_fail_self_verifier(tmp_path):
    pipeline, f = make_ok_pipeline(tmp_path)

    pipeline = DevelopmentPipeline(
        llm_planner=pipeline._llm_planner,
        code_analyzer=pipeline._analyzer,
        context_retriever=pipeline._retriever,
        patch_planner=pipeline._patch_planner,
        patch_generator=pipeline._patch_generator,
        self_verifier=FailingSelfVerifier(),
        trace=ExecutionTraceManager(),
    )

    req = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="a.txt", instructions="i")
    res = pipeline.run(req)

    assert res.success is False
    assert "verification" in (res.summary or "").lower()


def test_development_pipeline_early_stop_on_first_failure(tmp_path):
    # Prepare two ops where first will fail at generation
    f = tmp_path / "a.txt"
    f.write_text("A", encoding="utf-8")
    from clawai.editor import EditOperation
    op1 = EditOperation(file=str(f), original_content="A", new_content="B", reason="r")
    op2 = EditOperation(file=str(f), original_content="A", new_content="C", reason="r")
    plan = PatchPlan.success_plan((op1, op2), summary="two")

    pipeline = DevelopmentPipeline(
        llm_planner=FakeLLMPlanner(),
        code_analyzer=FakeAnalyzer(files=("a.txt",)),
        context_retriever=FakeRetriever(files=("a.txt",)),
        patch_planner=FakePatchPlanner(plan),
        patch_generator=FailingPatchGenerator(),
        self_verifier=SelfVerifier(patch_validator=PatchValidator(), rule_engine=RuleEngine(SelfVerifier.default_rules())),
        trace=ExecutionTraceManager(),
    )

    req = DevelopmentRequest(project_root=str(tmp_path), objective="o", target_query="a.txt", instructions="i")
    res = pipeline.run(req)

    assert res.success is False
    # Patches should be empty due to first op failure
    assert len(res.patches) == 0


def test_development_pipeline_determinism(tmp_path):
    pipeline, f = make_ok_pipeline(tmp_path)

    req = DevelopmentRequest(project_root=str(tmp_path), objective="obj", target_query="a.txt", instructions="i")
    r1 = pipeline.run(req)
    r2 = pipeline.run(req)

    assert r1 == r2
