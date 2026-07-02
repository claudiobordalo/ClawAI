from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace

import clawai.chat.chat_service as chat_service


class DummyWorkspaceManager:
    def __init__(self, *, current_root: str | None = None, tree_items=None, file_text: str | None = None) -> None:
        self._current_root = current_root
        self._tree_items = tree_items or []
        self._file_text = file_text

    def current(self):
        if self._current_root is None:
            raise RuntimeError("no workspace")
        return SimpleNamespace(root=self._current_root, workspace_id="ws-test")

    def tree(self, path: str = "", workspace_id: str | None = None):
        return self._tree_items

    def read_file(self, path: str, workspace_id: str | None = None):
        if self._file_text is None:
            raise FileNotFoundError(path)
        return self._file_text


def test_build_workspace_context_reports_when_no_workspace(monkeypatch) -> None:
    monkeypatch.setattr(chat_service, "workspace_manager", DummyWorkspaceManager())

    context = chat_service.ChatService().pipeline._build_workspace_context("O que existe nesse projeto?", None)

    assert context is not None
    assert "Nenhum workspace está aberto" in context


def test_build_workspace_context_uses_tree_for_project_queries(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        monkeypatch.setattr(
            chat_service,
            "workspace_manager",
            DummyWorkspaceManager(current_root=str(root), tree_items=[{"name": "src", "directory": True}, {"name": "README.md", "directory": False}]),
        )

        context = chat_service.ChatService().pipeline._build_workspace_context("O que existe nesse projeto?", None)

        assert "src" in context
        assert "README.md" in context


def test_build_workspace_context_reads_target_file(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        monkeypatch.setattr(
            chat_service,
            "workspace_manager",
            DummyWorkspaceManager(current_root=str(root), file_text="def main():\n    return 42"),
        )

        context = chat_service.ChatService().pipeline._build_workspace_context("Analise api.py", None)

        assert "def main" in context
        assert "api.py" in context
