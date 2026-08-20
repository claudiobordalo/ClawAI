from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .test_suite_result import TestSuiteResult


@dataclass(frozen=True)
class DiagnosisResult:
    success: bool
    probable_causes: Tuple[str, ...]
    failing_tests: Tuple[str, ...]
    summary: str


class TestDiagnosis:
    """Deterministic diagnosis engine for test suite results.

    It does not use LLMs. Uses simple rules to infer probable causes based on
    stderr/stdout messages and failing cases.
    """

    def diagnose(self, result: TestSuiteResult) -> DiagnosisResult:
        causes: List[str] = []
        failing: List[str] = [c.name for c in result.cases if c.status in ("failed", "error")]
        text = f"{result.stdout}\n{result.stderr}".lower()

        # Map known errors to probable causes
        mapping = [
            ("modulenotfounderror", "missing module or dependency"),
            ("importerror", "import failure"),
            ("assertionerror", "assertion failure in tests or code"),
            ("timeoutexpired", "test execution timed out"),
            ("syntaxerror", "syntax error in code"),
            ("filenotfounderror", "file not found during tests"),
            ("permissionerror", "permission denied while running tests"),
        ]
        for key, cause in mapping:
            if key in text and cause not in causes:
                causes.append(cause)

        # If return indicates success but there are skipped tests only
        if result.success and result.passed > 0 and result.failed == 0 and result.errors == 0:
            if result.skipped > 0 and "configuration" in text:
                causes.append("test configuration may skip some tests")

        # If nothing detected and not successful, provide generic summary
        if not causes and not result.success:
            if result.errors > 0:
                causes.append("errors occurred during test collection or execution")
            elif result.failed > 0:
                causes.append("one or more tests failed")

        summary = self._make_summary(result, causes, failing)
        return DiagnosisResult(
            success=result.success,
            probable_causes=tuple(causes),
            failing_tests=tuple(failing),
            summary=summary,
        )

    def _make_summary(self, r: TestSuiteResult, causes: List[str], failing: List[str]) -> str:
        base = f"passed={r.passed} failed={r.failed} errors={r.errors} skipped={r.skipped} duration={round(r.duration,3)}s"
        if causes:
            return base + "; causes: " + "; ".join(causes)
        return base + "; causes: none detected"
