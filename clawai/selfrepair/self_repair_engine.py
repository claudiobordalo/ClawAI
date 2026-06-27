from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional, List

from clawai.development.development_pipeline import DevelopmentPipeline
from clawai.development.development_request import DevelopmentRequest
from clawai.testing.test_runner import TestRunner
from clawai.testing.test_request import TestRequest
from clawai.testing.test_diagnosis import TestDiagnosis
from clawai.testing.test_suite_result import TestSuiteResult
from clawai.tracing.execution_trace import ExecutionTraceManager
from clawai.strategy.repair_strategy import RepairStrategy
from clawai.strategy.repair_context import RepairContext

from .repair_iteration import RepairIteration
from .repair_request import RepairRequest
from .repair_result import RepairResult


@dataclass(frozen=True)
class _Ops:
    start: str = "repair_iteration_started"
    dev: str = "development_completed"
    tests: str = "tests_completed"
    diag: str = "diagnosis_completed"
    finish: str = "repair_finished"


class SelfRepairEngine:
    def __init__(
        self,
        *,
        pipeline: DevelopmentPipeline,
        test_runner: TestRunner,
        diagnosis: TestDiagnosis,
        trace: Optional[ExecutionTraceManager] = None,
    ) -> None:
        self._pipeline = pipeline
        self._runner = test_runner
        self._diagnosis = diagnosis
        self._trace = trace
        self._ops = _Ops()
        self._strategy = RepairStrategy()

    def _start(self, op: str):
        if not self._trace:
            return None
        return self._trace.start("SelfRepair", op)

    def _finish(self, token, status: str, metadata: Optional[dict] = None):
        if token and self._trace:
            self._trace.finish(token, status=status, metadata=metadata or {})

    def _default_test_request(self, req: RepairRequest) -> TestRequest:
        # Use deterministic pytest invocation with -q for concise output
        py = sys.executable or "python"
        return TestRequest(project_root=req.project_root, command=(py, "-m", "pytest", "-q"), timeout=60)

    def run(self, request: RepairRequest) -> RepairResult:
        iterations: List[RepairIteration] = []
        try:
            current_instruction = request.instructions
            previous_diag = None
            previous_summary = None
            for i in range(1, request.max_iterations + 1):
                # Strategy decision before development
                ctx = RepairContext(
                    objective=request.objective,
                    original_instruction=request.instructions,
                    current_instruction=current_instruction,
                    iteration=i,
                    previous_diagnosis=previous_diag,
                    previous_summary=previous_summary,
                )
                decision = self._strategy.decide(ctx)
                self._log("strategy_decision", {"iteration": i, "reason": decision.reason})
                used_instructions = decision.updated_instruction

                t_start = self._start(self._ops.start)
                dev_res = None
                test_res: Optional[TestSuiteResult] = None
                diag_res = None
                try:
                    dev_res = self._pipeline.run(
                        DevelopmentRequest(
                            project_root=request.project_root,
                            objective=request.objective,
                            target_query=request.target_query,
                            instructions=used_instructions,
                        )
                    )
                    self._finish(t_start, "success", {"iteration": i, "stage": "development_started"})
                except Exception as e:
                    # Encapsulate and stop
                    self._finish(t_start, "failure", {"iteration": i, "error": type(e).__name__})
                    it = RepairIteration(iteration=i, development_result=None, test_result=None, diagnosis=None, success=False)
                    iterations.append(it)
                    return RepairResult(success=False, iterations=tuple(iterations), final_iteration=it, summary="development exception", error=str(e))

                # Development completed (regardless of success)
                self._log(self._ops.dev, {"iteration": i, "success": bool(getattr(dev_res, "success", False))})

                # Run tests
                try:
                    t_req = self._default_test_request(request)
                    test_res = self._runner.run(t_req)
                except Exception as e:
                    self._log(self._ops.tests, {"iteration": i, "error": type(e).__name__}, status="failure")
                    it = RepairIteration(iteration=i, development_result=dev_res, test_result=None, diagnosis=None, success=False)
                    iterations.append(it)
                    return RepairResult(success=False, iterations=tuple(iterations), final_iteration=it, summary="test runner exception", error=str(e))
                self._log(self._ops.tests, {"iteration": i, "success": bool(getattr(test_res, "success", False))})

                # Diagnose
                try:
                    diag_res = self._diagnosis.diagnose(test_res)
                except Exception as e:
                    self._log(self._ops.diag, {"iteration": i, "error": type(e).__name__}, status="failure")
                    it = RepairIteration(iteration=i, development_result=dev_res, test_result=test_res, diagnosis=None, success=False)
                    iterations.append(it)
                    return RepairResult(success=False, iterations=tuple(iterations), final_iteration=it, summary="diagnosis exception", error=str(e))
                self._log(self._ops.diag, {"iteration": i, "success": True})

                success = bool(getattr(test_res, "success", False))
                it = RepairIteration(iteration=i, development_result=dev_res, test_result=test_res, diagnosis=diag_res, success=success)
                iterations.append(it)

                # Prepare next iteration context data
                previous_diag = diag_res
                previous_summary = getattr(diag_res, "summary", None)
                current_instruction = used_instructions

                if success:
                    self._log(self._ops.finish, {"iterations": i, "result": "success"})
                    return RepairResult(success=True, iterations=tuple(iterations), final_iteration=it, summary=f"repaired in {i} iteration(s)")

            # Max iterations reached
            self._log(self._ops.finish, {"iterations": len(iterations), "result": "max_reached"})
            final = iterations[-1] if iterations else None
            return RepairResult(success=False, iterations=tuple(iterations), final_iteration=final, summary=f"max_iterations reached ({request.max_iterations})")
        except Exception as e:
            # Outer guard
            final = iterations[-1] if iterations else None
            self._log(self._ops.finish, {"iterations": len(iterations), "result": "exception"}, status="failure")
            return RepairResult(success=False, iterations=tuple(iterations), final_iteration=final, summary="self-repair exception", error=str(e))

    def _log(self, op: str, metadata: Optional[dict] = None, *, status: str = "success") -> None:
        t = self._start(op)
        self._finish(t, status, metadata or {})
