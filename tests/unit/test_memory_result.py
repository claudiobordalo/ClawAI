import pytest

from clawai.engineering import MemoryResult, EngineeringRecord
from datetime import datetime, timezone


def _rec(idx: int, success: bool = True) -> EngineeringRecord:
    return EngineeringRecord(
        timestamp=datetime.now(timezone.utc),
        objective=f"O{idx}",
        target_query=f"T{idx}",
        instructions="I",
        diagnosis="D",
        strategy="RepairStrategy",
        summary="S",
        success=success,
        modified_files=tuple(),
        failed_tests=tuple(),
        duration=0.1,
    )


def test_memory_result_creation_and_immutability():
    r1, r2 = _rec(1), _rec(2)
    mr = MemoryResult(records=(r1, r2), count=2)
    assert mr.count == 2 and len(mr.records) == 2

    with pytest.raises(ValueError):
        _ = MemoryResult(records=(r1,), count=2)
