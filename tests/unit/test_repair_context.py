import pytest

from clawai.strategy import RepairContext
from clawai.testing.test_diagnosis import DiagnosisResult


def test_repair_context_creation_and_immutability():
    diag = DiagnosisResult(success=False, probable_causes=("x",), failing_tests=("t::a",), summary="s")
    ctx = RepairContext(
        objective="o",
        original_instruction="base",
        current_instruction="base",
        iteration=1,
        previous_diagnosis=diag,
        previous_summary="sum",
    )
    assert ctx.iteration == 1 and ctx.objective == "o"
    with pytest.raises(Exception):
        ctx.iteration = 2
