from pathlib import Path
import pytest

from clawai.testing import TestRequest


def test_test_request_basic_and_immutability(tmp_path: Path):
    req = TestRequest(project_root=tmp_path, command=("python", "-V"), timeout=5.0)
    assert isinstance(req.project_root, Path)
    assert req.project_root == tmp_path
    assert isinstance(req.command, tuple)
    assert req.command[0] == "python"
    with pytest.raises(Exception):
        # Frozen dataclass should prevent assignment
        req.timeout = 1


def test_test_request_normalizes_command_from_string(tmp_path: Path):
    req = TestRequest(project_root=tmp_path, command="python -m pytest -q", timeout=5)
    assert req.command[:3] == ("python", "-m", "pytest")


def test_test_request_rejects_non_positive_timeout(tmp_path: Path):
    with pytest.raises(ValueError):
        TestRequest(project_root=tmp_path, command=("python", "-V"), timeout=0)
