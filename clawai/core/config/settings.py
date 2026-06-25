from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
    coder_model: str = "qwen2.5-coder:14b"
    reviewer_model: str = "deepseek-r1:8b"
    vision_model: str = "qwen2.5vl:7b"
    embedding_model: str = "nomic-embed-text"

    resource_cpu_busy_percent: float = 85.0
    resource_ram_busy_percent: float = 85.0
    resource_disk_busy_percent: float = 95.0
    critical_processes: tuple[str, ...] = (
        "gta5.exe",
        "dofus.exe",
        "ankama launcher.exe",
        "blender.exe",
        "unrealeditor.exe",
        "unity.exe",
        "cl.exe",
        "msbuild.exe",
        "ninja.exe",
    )

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

    def apply_config(
        self,
        config: dict[str, Any],
    ) -> None:
        """
        Aplica valores carregados sem expor o restante do sistema ao formato YAML.
        """
        application = config.get("application", {})
        paths = config.get("paths", {})
        ollama = config.get("ollama", {})
        models = config.get("models", {})
        resources = config.get("resources", {})

        if isinstance(application, dict):
            self.debug = bool(application.get("debug", self.debug))

        if isinstance(paths, dict):
            self.logs_path = self._resolve_path(paths.get("logs"), self.logs_path)
            self.memory_path = self._resolve_path(paths.get("memory"), self.memory_path)
            self.projects_path = self._resolve_path(
                paths.get("projects"),
                self.projects_path,
            )

        if isinstance(ollama, dict):
            self.ollama_host = str(ollama.get("host", self.ollama_host))

        if isinstance(models, dict):
            self.default_model = str(models.get("default", self.default_model))
            self.planner_model = str(models.get("planner", self.planner_model))
            self.coder_model = str(models.get("coder", self.coder_model))
            self.reviewer_model = str(models.get("reviewer", self.reviewer_model))
            self.vision_model = str(models.get("vision", self.vision_model))
            self.embedding_model = str(models.get("embedding", self.embedding_model))

        if isinstance(resources, dict):
            self.resource_cpu_busy_percent = float(
                resources.get("cpu_busy_percent", self.resource_cpu_busy_percent)
            )
            self.resource_ram_busy_percent = float(
                resources.get("ram_busy_percent", self.resource_ram_busy_percent)
            )
            self.resource_disk_busy_percent = float(
                resources.get("disk_busy_percent", self.resource_disk_busy_percent)
            )

            critical_processes = resources.get("critical_processes")

            if isinstance(critical_processes, list):
                self.critical_processes = tuple(
                    str(process).lower()
                    for process in critical_processes
                )

    def _resolve_path(
        self,
        value: object,
        default: Path,
    ) -> Path:
        if value is None:
            return default

        path = Path(str(value))

        if path.is_absolute():
            return path

        return self.root_path / path
