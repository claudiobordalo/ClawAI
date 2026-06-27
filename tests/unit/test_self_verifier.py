from __future__ import annotations

from pathlib import Path

from clawai.diffing import Patch, PatchValidator
from clawai.tracing.execution_trace import ExecutionTraceManager
from clawai.verification import RuleEngine, SelfVerifier, VerificationRule


def default_engine() -> RuleEngine:
    # Use default rules from SelfVerifier
    rules = SelfVerifier.default_rules()
    return RuleEngine(rules)


def test_self_verifier_full_flow_with_trace(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc", encoding="utf-8")

    patch = Patch(file=str(f), original="b", replacement="B", start_line=2, end_line=2, reason="r")
    trace = ExecutionTraceManager()
    verifier = SelfVerifier(patch_validator=PatchValidator(), rule_engine=default_engine(), trace=trace)

    res = verifier.verify([patch])

    assert res.success is True
    assert trace.size() >= 2  # two phases recorded

    # No disk write
    assert f.read_text(encoding="utf-8") == "a\nb\nc"


def test_self_verifier_validator_failure_stops(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc", encoding="utf-8")

    bad = Patch(file=str(f), original="WRONG", replacement="B", start_line=2, end_line=2, reason="r")

    verifier = SelfVerifier(patch_validator=PatchValidator(), rule_engine=default_engine())
    res = verifier.verify([bad])

    assert res.success is False
    assert res.checked_patches == 1
    assert res.passed_rules == 0 and res.failed_rules == 0


def test_self_verifier_rule_engine_failure(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("a\nb\nc", encoding="utf-8")

    p = Patch(file=str(f), original="b", replacement="B", start_line=2, end_line=2, reason="r")

    # Engine with a failing error-level rule
    engine = RuleEngine([
        VerificationRule("always_fail", "", "error", lambda p: (False, "boom"))
    ])

    verifier = SelfVerifier(patch_validator=PatchValidator(), rule_engine=engine)
    res = verifier.verify([p])

    assert res.success is False
    assert len(res.errors) == 1


def test_self_verifier_stop_on_critical_error(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x\ny\nz", encoding="utf-8")

    p1 = Patch(file=str(f), original="y", replacement="Y", start_line=2, end_line=2, reason="r")
    p2 = Patch(file=str(f), original="z", replacement="Z", start_line=3, end_line=3, reason="r")

    # First rule warns, second errors; engine stops at first error
    engine = RuleEngine([
        VerificationRule("warn", "", "warning", lambda p: (False, "w")),
        VerificationRule("err", "", "error", lambda p: (False, "e")),
        VerificationRule("never_reached", "", "error", lambda p: (True, "")),
    ])

    verifier = SelfVerifier(patch_validator=PatchValidator(), rule_engine=engine)
    res = verifier.verify([p1, p2])

    assert res.success is False
    # Only first patch checked due to early error
    assert res.checked_patches == 1
    assert res.failed_rules >= 1


def test_self_verifier_determinism(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("one\ntwo\nthree", encoding="utf-8")

    p = Patch(file=str(f), original="two", replacement="TWO", start_line=2, end_line=2, reason="r")

    verifier = SelfVerifier(patch_validator=PatchValidator(), rule_engine=default_engine())
    r1 = verifier.verify([p])
    r2 = verifier.verify([p])

    assert r1 == r2


def test_self_verifier_no_disk_writes(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("A\nB\nC", encoding="utf-8")
    original = f.read_text(encoding="utf-8")

    p = Patch(file=str(f), original="B", replacement="BB", start_line=2, end_line=2, reason="r")

    verifier = SelfVerifier(patch_validator=PatchValidator(), rule_engine=default_engine())
    _ = verifier.verify([p])

    assert f.read_text(encoding="utf-8") == original
