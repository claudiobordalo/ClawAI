from clawai.testing import TestParser


def test_parser_all_passed_output():
    stdout = """
============================= test session starts =============================
collected 3 items

test_example.py::test_a PASSED
test_example.py::test_b PASSED
test_example.py::test_c PASSED

============================== 3 passed in 0.12s ==============================
""".strip()
    p = TestParser()
    r = p.parse(stdout=stdout, stderr="", returncode=0)
    assert r.success is True
    assert r.passed == 3 and r.failed == 0 and r.errors == 0 and r.skipped == 0
    assert r.total == 3
    assert r.duration == 0.12
    assert len(r.cases) == 3


def test_parser_with_failures_output():
    stdout = """
============================= test session starts =============================
collected 2 items

test_example.py::test_a FAILED
test_example.py::test_b PASSED

================================ 1 failed, 1 passed in 0.50s ================================
""".strip()
    p = TestParser()
    r = p.parse(stdout=stdout, stderr="", returncode=1)
    assert r.success is False
    assert r.passed == 1 and r.failed == 1 and r.total == 2
    assert len(r.cases) == 2


def test_parser_empty_output_returns_valid_result():
    p = TestParser()
    r = p.parse(stdout="", stderr="", returncode=1)
    assert r.success is False
    assert r.total == 0
    assert r.stdout == "" and r.stderr == ""


def test_parser_unknown_output_is_safe_and_deterministic():
    out = "SOME TOOL OUTPUT WITHOUT PYTEST SUMMARY"
    p = TestParser()
    r1 = p.parse(stdout=out, stderr="", returncode=0)
    r2 = p.parse(stdout=out, stderr="", returncode=0)
    assert r1 == r2
    assert r1.success is True
    assert r1.total == 0
