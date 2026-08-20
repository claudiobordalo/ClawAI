from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any


LANGUAGE_HINTS = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".sh": "shell",
    ".ps1": "powershell",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
}

FRAMEWORK_FILES = {
    "pyproject.toml": ["python"],
    "requirements.txt": ["python"],
    "package.json": ["javascript", "typescript"],
    "tsconfig.json": ["typescript"],
    "Cargo.toml": ["rust"],
    "go.mod": ["go"],
    "pom.xml": ["java"],
    "build.gradle": ["java"],
    "build.gradle.kts": ["java"],
    "csproj": ["csharp"],
}

TEST_FILES = {
    "pytest.ini": "pytest",
    "tox.ini": "pytest",
    "unittest": "unittest",
    "package.json": "npm test",
    "Cargo.toml": "cargo test",
    "go.mod": "go test",
    "pom.xml": "maven test",
    "build.gradle": "gradle test",
    "build.gradle.kts": "gradle test",
}


@dataclass(slots=True)
class ProjectMap:
    root: str
    language_counts: dict[str, int] = field(default_factory=dict)
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    readme_files: list[str] = field(default_factory=list)
    files: int = 0
    directories: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ProjectAnalyzer:
    def analyze(self, root: str | Path, *, max_files: int = 2500) -> ProjectMap:
        root_path = Path(root).expanduser().resolve()
        result = ProjectMap(root=str(root_path))

        if not root_path.exists() or not root_path.is_dir():
            return result

        seen_languages: dict[str, int] = {}
        frameworks: set[str] = set()
        test_commands: set[str] = set()
        entrypoints: list[str] = []
        config_files: list[str] = []
        readme_files: list[str] = []
        files = 0
        directories = 0

        for path in root_path.rglob("*"):
            if files >= max_files:
                break
            if path.name.startswith(".") and path.name not in {".gitignore", ".env", ".env.example"}:
                continue
            if path.is_dir():
                directories += 1
                continue

            files += 1
            rel = path.relative_to(root_path).as_posix()
            suffix = path.suffix.lower()
            name = path.name.lower()

            language = LANGUAGE_HINTS.get(suffix)
            if language:
                seen_languages[language] = seen_languages.get(language, 0) + 1

            if name.startswith("readme") or suffix == ".md":
                readme_files.append(rel)

            if name in {"main.py", "app.py", "run.py", "server.py", "index.js", "index.ts", "index.tsx", "main.tsx", "main.jsx"}:
                entrypoints.append(rel)

            if name in {"pytest.ini", "tox.ini", "requirements.txt", "package.json", "Cargo.toml", "go.mod", "pyproject.toml", "pom.xml", "build.gradle", "build.gradle.kts", "tsconfig.json"}:
                config_files.append(rel)

            if name in FRAMEWORK_FILES:
                for fw in FRAMEWORK_FILES[name]:
                    frameworks.add(fw)

            if name in TEST_FILES:
                test_commands.add(TEST_FILES[name])

            if suffix == ".py" and ("test" in name or rel.startswith("tests/") or rel.startswith("test/")):
                test_commands.add("pytest")

            if suffix in {".js", ".jsx", ".ts", ".tsx"} and ("test" in name or rel.startswith("tests/") or rel.startswith("test/")):
                test_commands.add("npm test")

        result.language_counts = dict(sorted(seen_languages.items(), key=lambda item: (-item[1], item[0])))
        result.languages = list(result.language_counts.keys())
        result.frameworks = sorted(frameworks)
        result.test_commands = sorted(test_commands)
        result.entrypoints = sorted(set(entrypoints))
        result.config_files = sorted(set(config_files))
        result.readme_files = sorted(set(readme_files))
        result.files = files
        result.directories = directories
        return result
