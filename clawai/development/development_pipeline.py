from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from clawai.diffing import PatchGenerator, PatchResult
from clawai.patching import ChangeRequest, PatchPlanner
from clawai.planning.llm_planner import LLMPlanner
from clawai.tracing.execution_trace import ExecutionTraceManager
from clawai.verification import SelfVerifier

from .development_request import DevelopmentRequest
from .development_result import DevelopmentResult


@dataclass(frozen=True)
class _PhaseNames:
    plan: str = "plan"
    analyze: str = "analyze"
    retrieve: str = "retrieve"
    patch_plan: str = "patch_plan"
    generate_patches: str = "generate_patches"
    verify_patches: str = "verify_patches"


class DevelopmentPipeline:
    """Runs the full development cycle up to patch verification (no writes)."""

    def __init__(
        self,
        *,
        llm_planner: LLMPlanner,
        code_analyzer: object,
        context_retriever: object,
        patch_planner: PatchPlanner,
        patch_generator: PatchGenerator,
        self_verifier: SelfVerifier,
        trace: Optional[ExecutionTraceManager] = None,
    ) -> None:
        self._llm_planner = llm_planner
        self._analyzer = code_analyzer
        self._retriever = context_retriever
        self._patch_planner = patch_planner
        self._patch_generator = patch_generator
        self._self_verifier = self_verifier
        self._trace = trace
        self._phases = _PhaseNames()

    def run(self, request: DevelopmentRequest) -> DevelopmentResult:
        try:
            # Phase: LLM Planner
            t1 = self._start(self._phases.plan)
            plan_res = self._llm_planner.create_plan(request.objective)
            if not getattr(plan_res, "success", False) or getattr(plan_res, "plan", None) is None:
                self._finish(t1, "failure", {"error": getattr(plan_res, "error", "planning failed")})
                return DevelopmentResult.fail(summary="LLM planning failed", error=getattr(plan_res, "error", None))
            exec_plan = plan_res.plan
            self._finish(t1, "success", {"steps": len(getattr(exec_plan, "steps", ()))})

            # Phase: Code Analyzer (for deterministic pipeline tracing; output not reused by PatchPlanner)
            t2 = self._start(self._phases.analyze)
            snapshot = self._analyzer.analyze(request.project_root)
            self._finish(t2, "success", {"files": len(getattr(snapshot, "files", ()))})

            # Phase: Context Retriever
            t3 = self._start(self._phases.retrieve)
            retrieval = self._retriever.retrieve(snapshot, request.target_query)
            files = tuple(getattr(retrieval, "files", ()))
            self._finish(t3, "success", {"files": len(files)})

            # Phase: Patch Planner (uses its own analyzer/retriever internally per architecture)
            t4 = self._start(self._phases.patch_plan)
            change_request = ChangeRequest(
                objective=request.objective,
                target_query=request.target_query,
                instructions=request.instructions,
            )
            patch_plan = self._patch_planner.plan(change_request, request.project_root)
            if not getattr(patch_plan, "success", False):
                self._finish(t4, "failure", {"error": getattr(patch_plan, "error", "patch planning failed")})
                return DevelopmentResult.fail(
                    summary="Patch planning failed",
                    error=getattr(patch_plan, "error", None),
                    execution_plan=exec_plan,
                    patch_plan=patch_plan,
                )
            self._finish(t4, "success", {"ops": len(getattr(patch_plan, "operations", ()))})

            # Phase: Patch Generation
            t5 = self._start(self._phases.generate_patches)
            patches_accum: List = []
            for op in patch_plan.operations:
                pres: PatchResult = self._patch_generator.generate(op)
                if not pres.success:
                    self._finish(t5, "failure", {"error": pres.error or "patch generation failed"})
                    return DevelopmentResult.fail(
                        summary="Patch generation failed",
                        error=pres.error,
                        execution_plan=exec_plan,
                        patch_plan=patch_plan,
                        patches=tuple(patches_accum),
                    )
                patches_accum.extend(pres.patches)
            patches_tuple = tuple(patches_accum)
            self._finish(t5, "success", {"patches": len(patches_tuple)})

            # Phase: Self Verification
            t6 = self._start(self._phases.verify_patches)
            verification = self._self_verifier.verify(patches_tuple)
            if not verification.success:
                self._finish(t6, "failure", {"errors": len(verification.errors)})
                return DevelopmentResult.fail(
                    summary="Verification failed",
                    error=", ".join(verification.errors) if verification.errors else "verification failed",
                    execution_plan=exec_plan,
                    patch_plan=patch_plan,
                    patches=patches_tuple,
                    verification=verification,
                )
            self._finish(t6, "success", {"passed": verification.passed_rules, "failed": verification.failed_rules})

            return DevelopmentResult.ok(
                execution_plan=exec_plan,
                patch_plan=patch_plan,
                patches=patches_tuple,
                verification=verification,
                summary="Pipeline completed successfully",
            )
        except Exception as e:
            return DevelopmentResult.fail(summary="Pipeline error", error=str(e))

    # Trace helpers
    def _start(self, op: str):
        if not self._trace:
            return None
        return self._trace.start("DevelopmentPipeline", op)

    def _finish(self, token, status: str, metadata: Optional[dict] = None):
        if token and self._trace:
            self._trace.finish(token, status=status, metadata=metadata or {})
