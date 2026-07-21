from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    checked_patches: int
    passed_rules: int
    failed_rules: int
    warnings: Tuple[str, ...]
    errors: Tuple[str, ...]

    @staticmethod
    def ok(checked_patches: int, passed: int, failed: int, warnings: Tuple[str, ...]) -> "VerificationResult":
        return VerificationResult(
            success=True,
            checked_patches=checked_patches,
            passed_rules=passed,
            failed_rules=failed,
            warnings=warnings,
            errors=tuple(),
        )

    @staticmethod
    def fail(checked_patches: int, passed: int, failed: int, warnings: Tuple[str, ...], errors: Tuple[str, ...]) -> "VerificationResult":
        return VerificationResult(
            success=False,
            checked_patches=checked_patches,
            passed_rules=passed,
            failed_rules=failed,
            warnings=warnings,
            errors=errors,
        )
