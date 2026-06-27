from __future__ import annotations

import pytest

from clawai.diffing import Patch
from clawai.verification import VerificationRule


def test_verification_rule_creation_and_immutability():
    def evaluator(p: Patch):
        return True, "ok"

    rule = VerificationRule(name="R1", description="desc", severity="error", evaluator=evaluator)
    assert rule.name == "R1"
    assert rule.description == "desc"
    assert rule.severity == "error"
    ok, _ = rule.evaluator(Patch(file="a", original="x", replacement="y", start_line=1, end_line=1, reason="r"))
    assert ok is True

    with pytest.raises(Exception):
        rule.name = "X"  # type: ignore[attr-defined]
