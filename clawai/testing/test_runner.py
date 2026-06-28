from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from clawai.tracing.execution_trace import ExecutionTraceManager

from .test_parser import TestParser
from .test_request import TestRequest
from .test_suite_result import TestSuiteResult


@dataclass(frozen=True)
class _RunEnvelope:
    __test__ = False
    stdout: str
    stderr: str
    returncode: int
    duration: float


class TestRunner:
    __test__ = False
    """Executes a test suite command and parses results.

    Responsibilities:
    - Run subprocess.run with configurable timeout, cwd=project_root, capture_output=True, text=True
    - Never raise exceptions; always return TestSuiteResult
    - Register ExecutionTrace when provided
    """

    def __init__(self, trace: Optional[ExecutionTraceManager] = None) -> None:
        self._trace = trace
        self._parser = TestParser()

    def _execute(self, req: TestRequest) -> _RunEnvelope:
        start = time.perf_counter()
        tkn = self._trace.start("TestRunner", "run") if self._trace else None
        try:
            completed = subprocess.run(
                req.command,
                cwd=str(req.project_root),
                timeout=req.timeout,
                capture_output=True,
                text=True,
            )
            duration = time.perf_counter() - start
            if tkn:
                self._trace.finish(tkn, status="success", metadata={
                    "returncode": completed.returncode,
                    "duration_ms": round(duration * 1000, 3),
                })
            return _RunEnvelope(
                stdout=completed.stdout or "",
                stderr=completed.stderr or "",
                returncode=completed.returncode,
                duration=duration,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.perf_counter() - start
            if tkn:
                self._trace.finish(tkn, status="failure", metadata={
                    "error": "TimeoutExpired",
                    "duration_ms": round(duration * 1000, 3),
                })
            return _RunEnvelope(stdout=e.stdout or "", stderr=(e.stderr or str(e)), returncode=124, duration=duration)
        except FileNotFoundError as e:
            duration = time.perf_counter() - start
            if tkn:
                self._trace.finish(tkn, status="failure", metadata={
                    "error": "FileNotFoundError",
                    "duration_ms": round(duration * 1000, 3),
                })
            return _RunEnvelope(stdout="", stderr=str(e), returncode=127, duration=duration)
        except PermissionError as e:
            duration = time.perf_counter() - start
            if tkn:
                self._trace.finish(tkn, status="failure", metadata={
                    "error": "PermissionError",
                    "duration_ms": round(duration * 1000, 3),
                })
            return _RunEnvelope(stdout="", stderr=str(e), returncode=126, duration=duration)
        except Exception as e:
            duration = time.perf_counter() - start
            if tkn:
                self._trace.finish(tkn, status="failure", metadata={
                    "error": type(e).__name__,
                    "duration_ms": round(duration * 1000, 3),
                })
            # Generic failure envelope
            return _RunEnvelope(stdout="", stderr=str(e), returncode=1, duration=duration)

    def run(self, req: TestRequest) -> TestSuiteResult:
        env = self._execute(req)
        # Parse under trace
        tkn = self._trace.start("TestParser", "parse") if self._trace else None
        result = self._parser.parse(env.stdout, env.stderr, env.returncode)
        # Overwrite measured duration if parser inferred one; otherwise use measured
        duration = result.duration if result.duration > 0 else env.duration
        if tkn:
            self._trace.finish(tkn, status="success", metadata={
                "cases": len(result.cases),
                "passed": result.passed,
                "failed": result.failed,
                "errors": result.errors,
                "skipped": result.skipped,
            })
        # Return a new TestSuiteResult with the accurate duration
        return TestSuiteResult(
            success=result.success,
            total=result.total,
            passed=result.passed,
            failed=result.failed,
            skipped=result.skipped,
            errors=result.errors,
            duration=duration,
            stdout=env.stdout,
            stderr=env.stderr,
            cases=result.cases,
        )
