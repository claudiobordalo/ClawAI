from clawai.strategy import RepairStrategy, RepairContext
from clawai.testing.test_diagnosis import DiagnosisResult


def _ctx_no_diag():
    return RepairContext(
        objective="o",
        original_instruction="do base thing",
        current_instruction="do base thing",
        iteration=1,
        previous_diagnosis=None,
        previous_summary=None,
    )


def _ctx_with_diag(causes, summary="failed"):
    d = DiagnosisResult(success=False, probable_causes=tuple(causes), failing_tests=("t::a",), summary=summary)
    return RepairContext(
        objective="o",
        original_instruction="fix the tests",
        current_instruction="fix the tests",
        iteration=2,
        previous_diagnosis=d,
        previous_summary=summary,
    )


def test_strategy_no_diagnosis_returns_original():
    s = RepairStrategy()
    c = _ctx_no_diag()
    r = s.decide(c)
    assert r.updated_instruction == c.original_instruction


def test_strategy_modulenotfounderror():
    s = RepairStrategy()
    c = _ctx_with_diag(["ModuleNotFoundError"], summary="mod missing")
    r = s.decide(c)
    assert "Objective:" in r.updated_instruction
    assert "ModuleNotFoundError" in r.updated_instruction
    assert "Do not repeat the same error" in r.updated_instruction


def test_strategy_assertionerror():
    s = RepairStrategy()
    c = _ctx_with_diag(["AssertionError"], summary="assert failed")
    r = s.decide(c)
    assert "AssertionError" in r.updated_instruction


def test_strategy_syntaxerror():
    s = RepairStrategy()
    c = _ctx_with_diag(["SyntaxError"], summary="syntax bad")
    r = s.decide(c)
    assert "SyntaxError" in r.updated_instruction


def test_strategy_timeout():
    s = RepairStrategy()
    c = _ctx_with_diag(["TimeoutExpired"], summary="timeout")
    r = s.decide(c)
    assert "TimeoutExpired" in r.updated_instruction


def test_strategy_multiple_diagnoses_and_determinism():
    s = RepairStrategy()
    c = _ctx_with_diag(["AssertionError", "ModuleNotFoundError", "AssertionError"], summary="mix")
    a = s.decide(c)
    b = s.decide(c)
    assert a.updated_instruction == b.updated_instruction
    assert "AssertionError" in a.updated_instruction and "ModuleNotFoundError" in a.updated_instruction
