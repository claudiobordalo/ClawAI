from __future__ import annotations

import pytest

from clawai.diffing import Patch


def test_patch_creation_and_immutability():
    p = Patch(file="a.txt", original="x", replacement="y", start_line=2, end_line=2, reason="r")
    assert p.file == "a.txt"
    assert p.original == "x"
    assert p.replacement == "y"
    assert p.start_line == 2
    assert p.end_line == 2
    assert p.reason == "r"

    with pytest.raises(Exception):
        p.start_line = 5  # type: ignore[attr-defined]
