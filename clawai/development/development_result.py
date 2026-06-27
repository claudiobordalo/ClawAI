from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from clawai.diffing import Patch
from clawai.patching.patch_plan import PatchPlan
from clawai.planning.planner import ExecutionPlan
from clawai.verification.verification_result import VerificationResult


@dataclass(frozen=True)
class DevelopmentResult:
    success: bool
    execution_plan: Optional[ExecutionPlan]
    patch_plan: Optional[PatchPlan]
    patches: Tuple[Patch, ...]
    verification: Optional[VerificationResult]
    summary: str
    error: Optional[str] = None

    @staticmethod
    def ok(
        *,
        execution_plan: ExecutionPlan,
        patch_plan: PatchPlan,
        patches: Tuple[Patch, ...],
        verification: VerificationResult,
        summary: str = "",
    ) -> "DevelopmentResult":
        return DevelopmentResult(
            success=True,
            execution_plan=execution_plan,
            patch_plan=patch_plan,
            patches=patches,
            verification=verification,
            summary=summary,
            error=None,
        )

    @staticmethod
    def fail(
        *,
        summary: str = "",
        error: str | None = None,
        execution_plan: Optional[ExecutionPlan] = None,
        patch_plan: Optional[PatchPlan] = None,
        patches: Tuple[Patch, ...] = tuple(),
        verification: Optional[VerificationResult] = None,
    ) -> "DevelopmentResult":
        return DevelopmentResult(
            success=False,
            execution_plan=execution_plan,
            patch_plan=patch_plan,
            patches=patches,
            verification=verification,
            summary=summary,
            error=error,
        )
