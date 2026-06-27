from clawai.testing import TestDiagnosis, TestSuiteResult, TestCaseResult


def _base(stdout: str = "", stderr: str = "", success: bool = False, failed: int = 0, errors: int = 0):
    return TestSuiteResult(
        success=success,
        total=failed + errors,
        passed=0,
        failed=failed,
        skipped=0,
        errors=errors,
        duration=0.0,
        stdout=stdout,
        stderr=stderr,
        cases=(
            TestCaseResult(name="t::a", status="failed", duration=0.0) if failed else None,
        ) if (failed > 0) else tuple(),
    )


def test_diagnosis_module_not_found():
    d = TestDiagnosis()
    r = d.diagnose(_base(stderr="ModuleNotFoundError: no module named 'x'", errors=1))
    assert any("missing module" in c for c in r.probable_causes)


def test_diagnosis_import_error():
    d = TestDiagnosis()
    r = d.diagnose(_base(stderr="ImportError: cannot import name 'y'", errors=1))
    assert any("import failure" in c for c in r.probable_causes)


def test_diagnosis_assertion_error():
    d = TestDiagnosis()
    r = d.diagnose(_base(stdout="E   AssertionError: expected 1 == 2", failed=1))
    assert any("assertion" in c for c in r.probable_causes)


def test_diagnosis_timeout():
    d = TestDiagnosis()
    r = d.diagnose(_base(stderr="TimeoutExpired: command timed out", errors=1))
    assert any("timed out" in c for c in r.probable_causes)


def test_diagnosis_syntax_error():
    d = TestDiagnosis()
    r = d.diagnose(_base(stderr="SyntaxError: invalid syntax", errors=1))
    assert any("syntax error" in c for c in r.probable_causes)


def test_diagnosis_multiple_errors():
    d = TestDiagnosis()
    std = "ModuleNotFoundError: x\nImportError: y\nAssertionError: z"
    r = d.diagnose(_base(stdout=std, failed=1, errors=1))
    assert len(r.probable_causes) >= 2


def test_diagnosis_no_errors_success():
    d = TestDiagnosis()
    r = TestSuiteResult(success=True, total=2, passed=2, failed=0, skipped=0, errors=0, duration=0.1, stdout="", stderr="", cases=tuple())
    out = d.diagnose(r)
    assert out.success is True
    assert out.probable_causes == tuple()


def test_diagnosis_determinism():
    d = TestDiagnosis()
    r = _base(stderr="ImportError: x", errors=1)
    a = d.diagnose(r)
    b = d.diagnose(r)
    assert a == b
