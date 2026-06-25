from __future__ import annotations

from pathlib import Path

import pytest

from clawai.context.context_builder import ContextBuilder


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_incremental_build_selects_relevant_files(tmp_path: Path) -> None:
    # Estrutura (raiz)
    _write(tmp_path / "agents" / "patch_agent.py", "print('patch')\n")
    _write(tmp_path / "core" / "other.py", "print('core')\n")
    _write(tmp_path / "memory" / "secret.py", "print('memory_secret')\n")
    _write(tmp_path / "tests" / "test_x.py", "print('test')\n")

    builder = ContextBuilder()

    result = builder.incremental_build(
        project=tmp_path,
        objective="PatchAgent deve usar incremental context builder",
        max_files=5,
        max_chars=10_000,
    )

    # Deve incluir pelo menos algo relacionado a agentes
    # (heurística por tokens => agents/patch)
    assert any(
        name.endswith("agents/patch_agent.py")
        for name in result.selected_files
    )

    # Deve manter o contexto em string
    assert isinstance(result.context, str)
    assert len(result.context) > 0


def test_incremental_build_respects_max_files(tmp_path: Path) -> None:
    _write(tmp_path / "agents" / "a1.py", "1\n")
    _write(tmp_path / "agents" / "a2.py", "2\n")
    _write(tmp_path / "agents" / "a3.py", "3\n")
    _write(tmp_path / "core" / "c1.py", "4\n")

    builder = ContextBuilder()

    result = builder.incremental_build(
        project=tmp_path,
        objective="agents core",
        max_files=2,
        max_chars=10_000,
    )

    assert len(result.selected_files) <= 2

