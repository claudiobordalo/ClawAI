from __future__ import annotations

import re
from typing import Iterable, List, Tuple

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

from .test_case_result import TestCaseResult
from .test_suite_result import TestSuiteResult


class TestParser:
    """Parses pytest output to a structured TestSuiteResult.

    Only standard library is used. It never raises exceptions; on any parsing
    issue, it returns a conservative TestSuiteResult preserving stdout/stderr.
    """

    _COUNT_RE = re.compile(
        r"(?:(?P<failed>\d+)\s+failed)?(?:,\s*)?"
        r"(?:(?P<passed>\d+)\s+passed)?(?:,\s*)?"
        r"(?:(?P<skipped>\d+)\s+skipped)?(?:,\s*)?"
        r"(?:(?P<errors>\d+)\s+error[s]?)?",
        re.IGNORECASE,
    )
    _DURATION_RE = re.compile(r"in\s+(?P<secs>[0-9]+(?:\.[0-9]+)?)s", re.IGNORECASE)

    _CASE_LINE_RE = re.compile(
        r"^(?P<name>[^\s]+::[^\s]+)\s+(?P<status>PASSED|FAILED|SKIPPED|ERROR)(?:\s+\[(?P<sec>[0-9\.]+)s\])?",
        re.IGNORECASE,
    )

    def parse(self, stdout: str, stderr: str, returncode: int) -> TestSuiteResult:
        try:
            clean = _ANSI_RE.sub("", stdout or "")
            lines = clean.splitlines()
            cases: List[TestCaseResult] = []
            passed = failed = skipped = errors = 0
            duration = 0.0

            # Extract case lines when present (pytest -v style)
            for ln in lines:
                m = self._CASE_LINE_RE.match(ln.strip())
                if m:
                    name = m.group("name")
                    status = m.group("status").lower()
                    sec = float(m.group("sec")) if m.group("sec") else 0.0
                    if status == "passed":
                        passed += 1
                    elif status == "failed":
                        failed += 1
                    elif status == "skipped":
                        skipped += 1
                    elif status == "error":
                        errors += 1
                    cases.append(TestCaseResult(name=name, status=status, duration=sec))

            # Try to find summary information (supports both verbose and -q formats)
            sum_passed = sum_failed = sum_skipped = sum_errors = None
            sum_duration = None
            for ln in reversed(lines):
                body = ln
                # counts anywhere in the line
                cm = self._COUNT_RE.search(body)
                if cm:
                    if cm.group("passed"):
                        sum_passed = int(cm.group("passed"))
                    if cm.group("failed"):
                        sum_failed = int(cm.group("failed"))
                    if cm.group("skipped"):
                        sum_skipped = int(cm.group("skipped"))
                    if cm.group("errors"):
                        sum_errors = int(cm.group("errors"))
                dm = self._DURATION_RE.search(body)
                if dm:
                    sum_duration = float(dm.group("secs"))
                if (cm or dm) and ("passed" in body or "failed" in body or "error" in body or "skipped" in body or " in " in body):
                    # Likely the summary line; stop early
                    break

            # Reconcile counts: prefer summary if present; else use parsed case counts
            if sum_passed is not None or sum_failed is not None or sum_skipped is not None or sum_errors is not None:
                passed = sum_passed or 0
                failed = sum_failed or 0
                skipped = sum_skipped or 0
                errors = sum_errors or 0
            if sum_duration is not None:
                duration = sum_duration

            total = passed + failed + skipped + errors
            success = (returncode == 0) and (failed == 0) and (errors == 0)

            # If we couldn't parse any totals but command failed, reflect failure as generic error
            if total == 0 and returncode != 0:
                errors = max(errors, 1)
                success = False

            return TestSuiteResult(
                success=success,
                total=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
                stdout=stdout or "",
                stderr=stderr or "",
                cases=tuple(cases),
            )
        except Exception:
            # Fallback to safe envelope
            return TestSuiteResult(
                success=(returncode == 0),
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0 if returncode == 0 else 1,
                duration=0.0,
                stdout=stdout or "",
                stderr=stderr or "",
                cases=tuple(),
            )
