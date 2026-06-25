from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileContext:

    path: str
    language: str
    content: str


class Workspace:

    EXTENSIONS = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".cs": "csharp",
        ".java": "java",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
    }

    def load_project(
        self,
        root: str | Path,
    ) -> list[FileContext]:

        root = Path(root)

        files: list[FileContext] = []

        for file in root.rglob("*"):

            if not file.is_file():
                continue

            if any(part.startswith(".") for part in file.parts):
                continue

            language = self.EXTENSIONS.get(file.suffix.lower())

            if language is None:
                continue

            try:

                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

            except Exception:
                continue

            files.append(
                FileContext(
                    path=str(file.relative_to(root)).replace("\\", "/"),
                    language=language,
                    content=content,
                )
            )

        return files

    def build_context(
        self,
        root: str | Path,
        max_chars: int = 120000,
    ) -> str:

        project = self.load_project(root)

        context = []

        used = 0

        for file in project:

            block = f"""
========================
Arquivo: {file.path}
Linguagem: {file.language}
========================

{file.content}

"""

            if used + len(block) > max_chars:
                break

            context.append(block)

            used += len(block)

        return "\n".join(context)


workspace = Workspace()
