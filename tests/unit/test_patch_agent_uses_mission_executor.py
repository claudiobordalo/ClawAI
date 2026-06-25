from __future__ import annotations

from types import SimpleNamespace

from clawai.agents.patch_agent import PatchAgent


def test_patch_agent_generate_uses_mission_flow(monkeypatch) -> None:
    agent = PatchAgent()

    calls = {"ask": 0}

    def fake_ask(prompt: str, role=None, system_prompt=None) -> str:  # type: ignore[override]
        calls["ask"] += 1
        return """[
  {
    "path": "src/App.tsx",
    "operations": [
      { "type": "delete" }
    ]
  }
]"""

    monkeypatch.setattr(agent.router, "ask", fake_ask)

    # evita IO do Workspace
    import clawai.agents.patch_agent as patch_agent_module

    class FakeWorkspace:
        def open_project(self, project: str) -> None:
            return None

        def get_tree(self):
            return {"tree": "x"}

        def close_project(self) -> None:
            return None

    monkeypatch.setattr(patch_agent_module, "Workspace", FakeWorkspace)

    # evita IO/FS no Ignore/Scanner/FileReader
    class FakeIgnore:
        def __init__(self, project: str) -> None:
            pass

        def load(self) -> None:
            return None

    class FakeScanner:
        def __init__(self, project: str, ignore_engine=None) -> None:
            pass

    class FakeFileReader:
        def __init__(self) -> None:
            pass

    monkeypatch.setattr(patch_agent_module, "IgnoreEngine", FakeIgnore)
    monkeypatch.setattr(patch_agent_module, "Scanner", FakeScanner)
    monkeypatch.setattr(patch_agent_module, "FileReader", FakeFileReader)

    # evita leitura real no context builder
    def fake_build(*, objective: str, project_tree, scanner, file_reader, max_files: int, max_chars: int):
        return SimpleNamespace(context="CTX")

    monkeypatch.setattr(patch_agent_module, "context_builder", SimpleNamespace(build=fake_build))

    out = agent.generate("fake_project_root", "do thing")

    assert isinstance(out, list)
    assert calls["ask"] == 1
    assert out[0]["path"] == "src/App.tsx"
