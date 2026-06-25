from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from clawai.context.context_builder import ContextBuilder
from clawai.workspace.project_tree import ProjectNode, ProjectTree


class FakeScanner:
    def __init__(self, files: list[Path]) -> None:
        self._files = files
        self.list_files_calls = 0

    def list_files(self) -> list[Path]:
        self.list_files_calls += 1
        return list(self._files)


class FakeFileReader:
    def __init__(self, *, content_map: dict[Path, str]) -> None:
        self._content_map = content_map
        self.read_calls: list[tuple[Path, int | None]] = []

    def read_text(self, path: Path, *, max_chars: int | None = None, **_: object) -> str:
        # record calls
        self.read_calls.append((path, max_chars))
        content = self._content_map.get(path, "")

        if max_chars is None:
            return content
        return content[:max_chars]


def _project_tree(root: Path, *, dir_names: list[str]) -> ProjectTree:
    children: list[ProjectNode] = []
    for d in dir_names:
        children.append(ProjectNode(name=d, is_dir=True))
    root_node = ProjectNode(name=root.name, is_dir=True, children=tuple(children))
    return ProjectTree(root=root, root_node=root_node)


def test_context_builder_build_reads_only_relevant_dirs(tmp_path: Path) -> None:
    root = tmp_path

    # dirs: "pdf" should be relevant for objective containing PDF + related keywords
    tree = _project_tree(root, dir_names=["pdf", "core", "memory"])

    f_pdf = root / "pdf" / "a.pdf"
    f_irrelevant = root / "memory" / "secret.py"

    scanner = FakeScanner([f_irrelevant, f_pdf])
    file_reader = FakeFileReader(
        content_map={
            f_pdf: "PDF_CONTENT",
            f_irrelevant: "SHOULD_NOT_READ",
        },
    )

    builder = ContextBuilder()

    result = builder.build(
        objective="Gerar contexto para PDF document reader parser ocr",
        project_tree=tree,
        scanner=scanner,
        file_reader=file_reader,
        max_chars=2000,
        max_files=5,
    )

    read_paths = [p for (p, _mc) in file_reader.read_calls]
    assert f_irrelevant not in read_paths
    assert f_pdf in read_paths
    assert "PDF_CONTENT" in result.context


def test_context_builder_build_respects_max_chars_and_stops(tmp_path: Path) -> None:
    root = tmp_path
    tree = _project_tree(root, dir_names=["pdf", "core"])

    f1 = root / "pdf" / "a.pdf"
    f2 = root / "pdf" / "b.pdf"
    f3 = root / "pdf" / "c.pdf"

    scanner = FakeScanner([f1, f2, f3])
    file_reader = FakeFileReader(
        content_map={
            f1: "1" * 1000,
            f2: "2" * 1000,
            f3: "3" * 1000,
        },
    )

    builder = ContextBuilder()

    max_chars = 120
    result = builder.build(
        objective="PDF document reader parser ocr",
        project_tree=tree,
        scanner=scanner,
        file_reader=file_reader,
        max_chars=max_chars,
        max_files=10,
    )

    # resfriar: como bloco adiciona cabeçalho, não garantimos igualdade,
    # mas garantimos que o último remaining respeitou o limite.
    assert len(file_reader.read_calls) >= 1
    last_path, last_mc = file_reader.read_calls[-1]
    assert last_mc is not None
    assert last_mc <= max_chars

    # deve parar antes de ler tudo (há 3 arquivos, max_chars pequeno)
    assert len(file_reader.read_calls) < 3
    assert len(result.context) <= max_chars + 400  # margem para headers/joins


def test_context_builder_build_read_is_demanded(tmp_path: Path) -> None:
    root = tmp_path
    tree = _project_tree(root, dir_names=["pdf"])

    f1 = root / "pdf" / "a.pdf"
    f2 = root / "pdf" / "b.pdf"

    scanner = FakeScanner([f1, f2])
    file_reader = FakeFileReader(content_map={f1: "X" * 1000, f2: "Y" * 1000})

    builder = ContextBuilder()

    builder.build(
        objective="PDF reader parser ocr document",
        project_tree=tree,
        scanner=scanner,
        file_reader=file_reader,
        max_chars=10,
        max_files=1,
    )

    # “sob demanda”: com max_files=1, deve ler no máximo 1 arquivo
    assert len(file_reader.read_calls) == 1
    assert file_reader.read_calls[0][0] in {f1, f2}
