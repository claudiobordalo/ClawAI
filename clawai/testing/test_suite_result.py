from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .test_case_result import TestCaseResult


@dataclass(frozen=True)
class TestSuiteResult:
    __test__ = False
    """Immutable structured result of a test suite execution."""
    success: bool
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    stdout: str = ""
    stderr: str = ""
    cases: Tuple[TestCaseResult, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.total < 0 or self.passed < 0 or self.failed < 0 or self.skipped < 0 or self.errors < 0:
            raise ValueError("counts must be >= 0")
        if self.duration < 0:
            raise ValueError("duration must be >= 0")
        if self.total != self.passed + self.failed + self.skipped + self.errors and self.total != 0:
            # Allow total==0 for unknown totals
            raise ValueError("total must equal sum of passed+failed+skipped+errors when total > 0")
