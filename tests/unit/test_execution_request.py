from pathlib import Path
import pytest

from clawai.executor import ExecutionRequest


def test_execution_request_creation_and_immutability(tmp_path: Path):
    r = ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=2)
    assert r.project_root == tmp_path and r.max_iterations == 2
    with pytest.raises(Exception):
        r.max_iterations = 10


def test_execution_request_invalid_iterations(tmp_path: Path):
    with pytest.raises(ValueError):
        ExecutionRequest(project_root=tmp_path, objective="o", target_query="q", instructions="i", max_iterations=0)
