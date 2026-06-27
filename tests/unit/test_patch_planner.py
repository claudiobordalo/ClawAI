from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from clawai.codebase.project_snapshot import ProjectSnapshot, SourceFile
from clawai.patching import ChangeRequest, PatchPlanner
from clawai.providers.base import BaseProvider
from clawai.providers.base.response import ProviderResponse
from clawai.prompts.prompt_engine import PromptEngine


# Fakes determinísticos
class FakeAnalyzer:
    def __init__(self, files: tuple[str, ...]):
        self._files = files

    def analyze(self, root):
        abs_files = tuple(str(Path(root) / f) for f in self._files)
        sf = tuple(SourceFile(path=f, extension=Path(f).suffix) for f in abs_files)
        return ProjectSnapshot(root=str(Path(root)), files=sf)


@dataclass(frozen=True)
class FakeRetrieval:
    files: tuple[str, ...]


class FakeRetriever:
    def __init__(self, files: tuple[str, ...]):
        self._files = files

    def retrieve(self, snapshot, query):
        return FakeRetrieval(files=self._files)


class FakeProvider(BaseProvider):
    def __init__(self, content: str | Exception):
        self._content = content

    def generate(self, prompt: str, system_prompt: str | None = None) -> ProviderResponse:
        if isinstance(self._content, Exception):
            raise self._content
        return ProviderResponse(content=self._content, model="fake", provider="fake")


class FakeLLMPlanner:
    pass


def make_prompt_engine(provider):
    # Usa PromptEngine real para exercitar fluxo através do provider, com system prompt existente
    return PromptEngine(provider)


def test_patch_planner_single_operation(tmp_path):
    # Setup arquivos
    (tmp_path / "a.txt").write_text("OLD A", encoding="utf-8")

    analyzer = FakeAnalyzer(files=("a.txt",))
    retriever = FakeRetriever(files=("a.txt",))

    payload = {
        "summary": "Change one file",
        "operations": [
            {"file": "a.txt", "reason": "update", "new_content": "NEW A"}
        ],
    }
    provider = FakeProvider(json.dumps(payload))
    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="obj", target_query="a.txt", instructions="do it")
    plan = planner.plan(req, tmp_path)

    assert plan.success is True
    assert plan.summary == "Change one file"
    assert len(plan.operations) == 1
    op = plan.operations[0]
    assert Path(op.file) == tmp_path / "a.txt"
    assert op.original_content == "OLD A"
    assert op.new_content == "NEW A"
    assert op.reason == "update"
    # Nenhuma escrita em disco
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "OLD A"


def test_patch_planner_multiple_operations(tmp_path):
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")
    (tmp_path / "b.txt").write_text("B", encoding="utf-8")

    analyzer = FakeAnalyzer(files=("a.txt", "b.txt"))
    retriever = FakeRetriever(files=("b.txt", "a.txt"))  # ordem diferente para testar determinismo no prompt

    payload = {
        "summary": "Two changes",
        "operations": [
            {"file": "a.txt", "reason": "ra", "new_content": "NA"},
            {"file": "b.txt", "reason": "rb", "new_content": "NB"},
        ],
    }
    provider = FakeProvider(json.dumps(payload))
    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="o", target_query="q", instructions="i")
    p1 = planner.plan(req, tmp_path)
    p2 = planner.plan(req, tmp_path)

    assert p1 == p2  # determinismo
    assert p1.success is True and len(p1.operations) == 2


def test_patch_planner_invalid_json(tmp_path):
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")

    analyzer = FakeAnalyzer(files=("a.txt",))
    retriever = FakeRetriever(files=("a.txt",))
    provider = FakeProvider("not json")
    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="o", target_query="a.txt", instructions="i")
    plan = planner.plan(req, tmp_path)

    assert plan.success is False
    assert plan.error and "json" in plan.error.lower()


def test_patch_planner_provider_exception(tmp_path):
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")

    analyzer = FakeAnalyzer(files=("a.txt",))
    retriever = FakeRetriever(files=("a.txt",))
    provider = FakeProvider(RuntimeError("boom"))
    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="o", target_query="a.txt", instructions="i")
    plan = planner.plan(req, tmp_path)

    assert plan.success is False
    assert plan.error and "falhou" in plan.error.lower()


def test_patch_planner_missing_file(tmp_path):
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")

    analyzer = FakeAnalyzer(files=("a.txt",))
    retriever = FakeRetriever(files=("a.txt", "missing.txt"))

    payload = {
        "summary": "Invalid file",
        "operations": [
            {"file": "missing.txt", "reason": "r", "new_content": "X"},
        ],
    }
    provider = FakeProvider(json.dumps(payload))
    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="o", target_query="t", instructions="i")
    plan = planner.plan(req, tmp_path)

    assert plan.success is False
    assert plan.error and "arquivo" in plan.error.lower()


def test_patch_planner_empty_context(tmp_path):
    analyzer = FakeAnalyzer(files=tuple())
    retriever = FakeRetriever(files=tuple())

    provider = FakeProvider(json.dumps({"summary": "none", "operations": []}))
    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="o", target_query="t", instructions="i")
    plan = planner.plan(req, tmp_path)

    assert plan.success is False
    assert plan.error and "nenhum arquivo relevante" in plan.error.lower()


def test_patch_planner_no_disk_writes(tmp_path):
    (tmp_path / "a.txt").write_text("A", encoding="utf-8")
    analyzer = FakeAnalyzer(files=("a.txt",))
    retriever = FakeRetriever(files=("a.txt",))

    payload = {
        "summary": "Change",
        "operations": [
            {"file": "a.txt", "reason": "r", "new_content": "NEW"}
        ],
    }
    provider = FakeProvider(json.dumps(payload))
    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="o", target_query="a.txt", instructions="i")
    before = (tmp_path / "a.txt").read_text(encoding="utf-8")
    planner.plan(req, tmp_path)
    after = (tmp_path / "a.txt").read_text(encoding="utf-8")

    assert before == after


def test_patch_planner_full_integration(tmp_path):
    # Integra FakeAnalyzer + FakeRetriever + PromptEngine real + Provider fake
    (tmp_path / "a.txt").write_text("ORIG", encoding="utf-8")

    analyzer = FakeAnalyzer(files=("a.txt",))
    retriever = FakeRetriever(files=("a.txt",))

    payload = {
        "summary": "Integration",
        "operations": [
            {"file": "a.txt", "reason": "r", "new_content": "NEW"},
        ],
    }
    provider = FakeProvider(json.dumps(payload))

    planner = PatchPlanner(
        context_retriever=retriever,
        code_analyzer=analyzer,
        llm_planner=FakeLLMPlanner(),
        prompt_engine=make_prompt_engine(provider),
        provider=provider,
    )

    req = ChangeRequest(objective="o", target_query="a.txt", instructions="i")
    plan = planner.plan(req, tmp_path)

    assert plan.success is True
    assert plan.summary == "Integration"
    assert len(plan.operations) == 1
