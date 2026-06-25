from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """
    Configurações globais do ClawAI.
    """

    root_path: Path = Path.cwd()

    config_path: Path = field(init=False)
    data_path: Path = field(init=False)
    docs_path: Path = field(init=False)
    tests_path: Path = field(init=False)
    scripts_path: Path = field(init=False)

    logs_path: Path = field(init=False)
    memory_path: Path = field(init=False)
    projects_path: Path = field(init=False)

    ollama_host: str = "http://localhost:11434"

    default_model: str = "qwen2.5-coder:14b"
    planner_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"

    debug: bool = False

    def __post_init__(self) -> None:
        self.config_path = self.root_path / "configs"
        self.data_path = self.root_path / "data"
        self.docs_path = self.root_path / "docs"
        self.tests_path = self.root_path / "tests"
        self.scripts_path = self.root_path / "scripts"

        self.logs_path = self.data_path / "logs"
        self.memory_path = self.data_path / "memory"
        self.projects_path = self.data_path / "projects"