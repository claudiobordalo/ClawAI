from pathlib import Path
import pytest

from clawai.selfrepair import RepairRequest


def test_repair_request_creation_and_immutability(tmp_path: Path):
    r = RepairRequest(
        project_root=tmp_path,
        objective="fix failing tests",
        target_query="module::pattern",
        instructions="apply minimal patch",
        max_iterations=3,
    )
    assert r.project_root == tmp_path
    assert r.max_iterations == 3
    with pytest.raises(Exception):
        r.max_iterations = 10


def test_repair_request_invalid_iterations(tmp_path: Path):
    with pytest.raises(ValueError):
        RepairRequest(
            project_root=tmp_path,
            objective="o",
            target_query="q",
            instructions="i",
            max_iterations=0,
        )
