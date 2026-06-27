import pytest

from clawai.strategy import RepairDecision


def test_repair_decision_creation_and_immutability():
    d = RepairDecision(continue_execution=True, updated_instruction="i", reason="r")
    assert d.continue_execution is True and d.updated_instruction == "i"
    with pytest.raises(Exception):
        d.reason = "x"
