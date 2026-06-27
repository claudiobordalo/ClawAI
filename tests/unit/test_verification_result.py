from __future__ import annotations

import pytest

from clawai.verification import VerificationResult


def test_verification_result_creation_and_immutability():
    r = VerificationResult(success=True, checked_patches=2, passed_rules=3, failed_rules=0, warnings=("w",), errors=tuple())
    assert r.success is True
    assert r.checked_patches == 2
    assert r.passed_rules == 3
    assert r.failed_rules == 0
    assert r.warnings == ("w",)
    assert r.errors == tuple()

    with pytest.raises(Exception):
        r.success = False  # type: ignore[attr-defined]
