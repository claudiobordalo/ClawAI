from __future__ import annotations

from clawai.diffing import Patch
from clawai.verification import RuleEngine, VerificationRule


def make_patch() -> Patch:
    return Patch(file="a.txt", original="x", replacement="y", start_line=1, end_line=1, reason="r")


def test_rule_engine_pass_rule():
    rule = VerificationRule("pass", "", "error", lambda p: (True, "ok"))
    engine = RuleEngine([rule])

    res = engine.verify([make_patch()])
    assert res.success is True
    assert res.passed_rules == 1
    assert res.failed_rules == 0


def test_rule_engine_fail_rule_error():
    rule = VerificationRule("fail", "", "error", lambda p: (False, "bad"))
    engine = RuleEngine([rule])

    res = engine.verify([make_patch()])
    assert res.success is False
    assert res.failed_rules == 1
    assert len(res.errors) == 1 and "fail" in res.errors[0]


def test_rule_engine_multiple_rules_and_warnings():
    r1 = VerificationRule("w", "", "warning", lambda p: (False, "warn"))
    r2 = VerificationRule("p", "", "error", lambda p: (True, "ok"))
    engine = RuleEngine([r1, r2])

    res = engine.verify([make_patch()])
    assert res.success is True  # no error-level failures
    assert res.failed_rules == 1 and len(res.warnings) == 1
    assert res.passed_rules == 1


def test_rule_engine_multiple_patches():
    r = VerificationRule("p", "", "error", lambda p: (True, "ok"))
    engine = RuleEngine([r])

    res = engine.verify([make_patch(), make_patch()])
    assert res.success is True
    assert res.checked_patches == 2
    assert res.passed_rules == 2


def test_rule_engine_determinism():
    r = VerificationRule("p", "", "error", lambda p: (True, "ok"))
    engine = RuleEngine([r])

    p = [make_patch(), make_patch()]
    r1 = engine.verify(p)
    r2 = engine.verify(p)

    assert r1 == r2
