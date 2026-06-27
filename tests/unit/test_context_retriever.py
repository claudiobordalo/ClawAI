from __future__ import annotations

from pathlib import Path

from clawai.codebase import CodeAnalyzer
from clawai.retrieval import ContextRetriever, RetrievalResult


def _build_repo(tmp: Path) -> Path:
    (tmp / "planning").mkdir()
    (tmp / "agent").mkdir()
    (tmp / "planning" / "planner.py").write_text(
        """
class Planner:
    def run(self):
        pass
        """
    )
    (tmp / "agent" / "agent_loop.py").write_text(
        """
class AgentLoop:
    pass
        """
    )
    (tmp / "readme.md").write_text("# example\n")
    return tmp


def test_context_retriever_by_file(tmp_path: Path) -> None:
    root = _build_repo(tmp_path)
    snap = CodeAnalyzer().analyze(root)

    retriever = ContextRetriever()
    result = retriever.retrieve(snap, "planner.py")
    assert isinstance(result, RetrievalResult)
    assert any(p.endswith("planning/planner.py") for p in result.files)
    assert result.score > 0


def test_context_retriever_by_symbol(tmp_path: Path) -> None:
    root = _build_repo(tmp_path)
    snap = CodeAnalyzer().analyze(root)

    retriever = ContextRetriever()
    result = retriever.retrieve(snap, "Planner")

    assert any(s.qualname == "Planner" and s.kind == "class" for s in result.symbols)
    assert result.score >= 20


def test_context_retriever_no_matches(tmp_path: Path) -> None:
    root = _build_repo(tmp_path)
    snap = CodeAnalyzer().analyze(root)

    retriever = ContextRetriever()
    r1 = retriever.retrieve(snap, "zzzz")
    r2 = retriever.retrieve(snap, "zzzz")

    assert r1.files == () and r1.symbols == () and r1.score == 0
    assert r1 == r2  # determinístico
