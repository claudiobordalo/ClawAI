from datetime import datetime, timezone
import pytest
from dataclasses import FrozenInstanceError

from clawai.engineering import EngineeringRecord


def test_engineering_record_creation_and_immutability():
    ts = datetime.now(timezone.utc)
    rec = EngineeringRecord(
        timestamp=ts,
        objective="Improve parser",
        target_query="tests/unit",
        instructions="Fix summary regex",
        diagnosis="passed=10 failed=0; causes: none detected",
        strategy="RepairStrategy",
        summary="repaired in 1 iteration(s)",
        success=True,
        modified_files=("clawai/testing/test_parser.py",),
        failed_tests=tuple(),
        duration=1.234,
    )
    assert rec.timestamp == ts
    assert rec.success is True
    assert isinstance(rec.modified_files, tuple) and rec.modified_files[0].endswith("test_parser.py")

    with pytest.raises(FrozenInstanceError):
        # frozen dataclass must not allow mutation
        setattr(rec, "success", False)
