from pathlib import Path

from clawai.workspace.services.project_analyzer import ProjectAnalyzer


def test_project_analyzer():

    root = Path(__file__).resolve().parents[2]

    summary = ProjectAnalyzer().analyze(root)

    assert summary.name == "ClawAI"
    assert summary.root == root
    assert summary.total_files > 0
    assert summary.total_directories > 0
    assert "Python" in summary.languages