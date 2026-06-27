import sys
from pathlib import Path

import pytest

from clawai.testing import TestRunner, TestRequest
from clawai.tracing.execution_trace import ExecutionTraceManager


PY = sys.executable


def write_pytest_project(root: Path, tests_content: str) -> None:
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_sample.py").write_text(tests_content, encoding="utf-8")


def test_runner_successful_execution(tmp_path: Path):
    write_pytest_project(tmp_path, """
import pytest

def test_ok1():
    assert 1 + 1 == 2

def test_ok2():
    assert 'a'.upper() == 'A'
""")
    req = TestRequest(project_root=tmp_path, command=(PY, "-m", "pytest", "-q"), timeout=30)
    r = TestRunner().run(req)
    assert r.success is True
    assert r.passed >= 2
    assert r.failed == 0 and r.errors == 0
    assert r.duration >= 0


def test_runner_timeout(tmp_path: Path):
    write_pytest_project(tmp_path, """
import time

def test_slow():
    time.sleep(2)
    assert True
""")
    req = TestRequest(project_root=tmp_path, command=(PY, "-m", "pytest", "-q"), timeout=0.5)
    r = TestRunner().run(req)
    assert r.success is False
    assert r.errors >= 1 or r.failed >= 1
    assert "TimeoutExpired" in (r.stderr or "") or r.duration >= 0.5


def test_runner_nonexistent_command(tmp_path: Path):
    req = TestRequest(project_root=tmp_path, command=("this_command_does_not_exist_12345",), timeout=2)
    r = TestRunner().run(req)
    assert r.success is False
    assert r.errors >= 1
    assert "No such file" in (r.stderr or "") or "not found" in (r.stderr or "").lower() or r.stderr != ""


def test_runner_stderr_capture(tmp_path: Path):
    # Use a simple python command producing stderr
    req = TestRequest(project_root=tmp_path, command=(PY, "-c", "import sys; sys.stderr.write('ERR\n')"), timeout=5)
    r = TestRunner().run(req)
    assert "ERR" in r.stderr


def test_runner_with_execution_trace(tmp_path: Path):
    write_pytest_project(tmp_path, """

def test_ok():
    assert True
""")
    trace = ExecutionTraceManager()
    req = TestRequest(project_root=tmp_path, command=(PY, "-m", "pytest", "-q"), timeout=10)
    _ = TestRunner(trace=trace).run(req)
    events = trace.events()
    # Expect at least two events: TestRunner.run and TestParser.parse
    assert any(e.component == "TestRunner" and e.operation == "run" for e in events)
    assert any(e.component == "TestParser" and e.operation == "parse" for e in events)


def test_runner_determinism(tmp_path: Path):
    write_pytest_project(tmp_path, """

def test_ok():
    assert True
""")
    req = TestRequest(project_root=tmp_path, command=(PY, "-m", "pytest", "-q"), timeout=10)
    r1 = TestRunner().run(req)
    r2 = TestRunner().run(req)
    assert r1.passed == r2.passed and r1.failed == r2.failed and r1.errors == r2.errors
