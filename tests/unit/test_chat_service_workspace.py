from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from clawai.cognition.pipeline import CognitionPipeline


def test_build_workspace_context_no_workspace() -> None:
    """Testa que _build_workspace_context retorna mensagem neutra quando não há workspace."""
    pipeline = CognitionPipeline()
    # workspace_path não está definido por padrão
    assert not hasattr(pipeline, "workspace_path") or pipeline.workspace_path is None

    context = pipeline._build_workspace_context("O que existe nesse projeto?")

    assert context is not None
    assert "não configurado" in context


def test_build_workspace_context_with_workspace() -> None:
    """Testa que _build_workspace_context retorna o path quando configurado."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        pipeline = CognitionPipeline()
        pipeline.workspace_path = str(root)

        context = pipeline._build_workspace_context("O que existe nesse projeto?")

        assert context is not None
        assert str(root) in context
