from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Optional

from clawai.selfrepair import SelfRepairEngine, RepairRequest, RepairResult
from clawai.editor import CodeEditor, EditOperation
from clawai.editor.edit_result import EditResult
from clawai.tracing.execution_trace import ExecutionTraceManager
from clawai.engineering import EngineeringMemory, EngineeringRecord

from .abstract_executor import AbstractExecutor
from .execution_request import ExecutionRequest
from .execution_result import ExecutionResult


class AutonomousExecutor(AbstractExecutor):
    def __init__(
        self,
        *,
        self_repair: SelfRepairEngine,
        editor: CodeEditor,
        trace: Optional[ExecutionTraceManager] = None,
        memory: Optional[EngineeringMemory] = None,
    ) -> None:
        self._self_repair = self_repair
        self._editor = editor
        self._trace = trace
        self._memory = memory

    def _start(self, op: str):
        if not self._trace:
            return None
        return self._trace.start("AutonomousExecutor", op)

    def _finish(self, token, status: str, metadata: Optional[dict] = None):
        if token and self._trace:
            self._trace.finish(token, status=status, metadata=metadata or {})

    def _save_memory(
        self,
        *,
        request: ExecutionRequest,
        rr: RepairResult,
        success: bool,
        modified_files: List[str],
        start_time: float,
    ) -> None:
        if not self._memory:
            return
        diagnosis_summary = ""
        failed_tests: List[str] = []
        if rr.final_iteration and rr.final_iteration.diagnosis is not None:
            diagnosis_summary = rr.final_iteration.diagnosis.summary
            failed_tests = list(rr.final_iteration.diagnosis.failing_tests)
        duration = max(0.0, time.perf_counter() - start_time)
        record = EngineeringRecord(
            timestamp=datetime.now(timezone.utc),
            objective=request.objective,
            target_query=request.target_query,
            instructions=request.instructions,
            diagnosis=diagnosis_summary,
            strategy="RepairStrategy",
            summary=rr.summary,
            success=success,
            modified_files=tuple(modified_files),
            failed_tests=tuple(failed_tests),
            duration=duration,
        )
        try:
            self._memory.add(record)
            t_mem = self._start("engineering_memory_saved")
            self._finish(
                t_mem,
                "success",
                {"success": success, "modified_files": tuple(modified_files)},
            )
        except Exception:
            t_mem = self._start("engineering_memory_saved")
            self._finish(
                t_mem,
                "failure",
                {"success": success, "modified_files": tuple(modified_files)},
            )

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        start_time = time.perf_counter()
        t0 = self._start("execution_started")
        try:
            rr = self._self_repair.run(
                RepairRequest(
                    project_root=request.project_root,
                    objective=request.objective,
                    target_query=request.target_query,
                    instructions=request.instructions,
                    max_iterations=request.max_iterations,
                )
            )
            ops_count = 0
            if (
                rr.success
                and rr.final_iteration
                and rr.final_iteration.development_result
                and rr.final_iteration.development_result.patch_plan
            ):
                ops_count = len(
                    getattr(
                        rr.final_iteration.development_result.patch_plan,
                        "operations",
                        (),
                    )
                )
            self._finish(
                t0,
                "success",
                {
                    "result": "self_repair_completed",
                    "success": rr.success,
                    "operations": ops_count,
                },
            )

            if not rr.success:
                self._save_memory(
                    request=request,
                    rr=rr,
                    success=False,
                    modified_files=[],
                    start_time=start_time,
                )
                return ExecutionResult(
                    success=False,
                    repair_result=rr,
                    applied_results=tuple(),
                    summary="self-repair failed",
                )

            dev = rr.final_iteration.development_result if rr.final_iteration else None
            patch_plan = getattr(dev, "patch_plan", None)
            operations: List[EditOperation] = (
                list(getattr(patch_plan, "operations", ())) if patch_plan else []
            )

            applied: List[EditResult] = []
            modified_files: List[str] = []
            for op in operations:
                t_apply = self._start("edit_applied")
                try:
                    res = self._editor.apply(op)
                    applied.append(res)
                    if res.success:
                        modified_files.append(str(op.file))
                    self._finish(
                        t_apply,
                        "success" if res.success else "failure",
                        {
                            "file": str(op.file),
                            "success": res.success,
                            "error": res.error,
                        },
                    )
                    if not res.success:
                        t_end = self._start("execution_finished")
                        self._finish(
                            t_end,
                            "failure",
                            {
                                "operations": len(applied),
                                "success": False,
                                "error": res.error or "edit failed",
                            },
                        )
                        self._save_memory(
                            request=request,
                            rr=rr,
                            success=False,
                            modified_files=modified_files,
                            start_time=start_time,
                        )
                        return ExecutionResult(
                            success=False,
                            repair_result=rr,
                            applied_results=tuple(applied),
                            summary="edit failed",
                            error=res.error or "edit failed",
                        )
                except Exception as e:
                    self._finish(
                        t_apply,
                        "failure",
                        {
                            "file": str(op.file),
                            "success": False,
                            "error": type(e).__name__,
                        },
                    )
                    t_end = self._start("execution_finished")
                    self._finish(
                        t_end,
                        "failure",
                        {"operations": len(applied), "success": False, "error": str(e)},
                    )
                    self._save_memory(
                        request=request,
                        rr=rr,
                        success=False,
                        modified_files=modified_files,
                        start_time=start_time,
                    )
                    return ExecutionResult(
                        success=False,
                        repair_result=rr,
                        applied_results=tuple(applied),
                        summary="editor exception",
                        error=str(e),
                    )

            t_end = self._start("execution_finished")
            self._finish(
                t_end, "success", {"operations": len(applied), "success": True}
            )
            self._save_memory(
                request=request,
                rr=rr,
                success=True,
                modified_files=modified_files,
                start_time=start_time,
            )
            return ExecutionResult(
                success=True,
                repair_result=rr,
                applied_results=tuple(applied),
                summary="execution completed successfully",
            )
        except Exception as e:
            self._finish(
                t0,
                "failure",
                {
                    "result": "self_repair_completed",
                    "success": False,
                    "error": type(e).__name__,
                },
            )
            t_end = self._start("execution_finished")
            self._finish(
                t_end, "failure", {"operations": 0, "success": False, "error": str(e)}
            )
            dummy = RepairResult(
                success=False,
                iterations=tuple(),
                final_iteration=None,
                summary="exception",
                error=str(e),
            )
            try:
                self._save_memory(
                    request=request,
                    rr=dummy,
                    success=False,
                    modified_files=[],
                    start_time=start_time,
                )
            except Exception:
                pass
            return ExecutionResult(
                success=False,
                repair_result=dummy,
                applied_results=tuple(),
                summary="autonomous executor exception",
                error=str(e),
            )
