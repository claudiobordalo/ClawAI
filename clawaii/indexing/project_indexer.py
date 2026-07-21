from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class IndexedFile:

    path: str
    language: str
    lines: int
    size: int
    sha256: str


class ProjectIndexer:

    EXTENSIONS = {
        ".py":"python",
        ".ts":"typescript",
        ".tsx":"typescript",
        ".js":"javascript",
        ".jsx":"javascript",
        ".cs":"csharp",
        ".java":"java",
        ".sql":"sql",
        ".json":"json",
        ".yaml":"yaml",
        ".yml":"yaml",
        ".md":"markdown",
        ".html":"html",
        ".css":"css",
    }

    def build(
        self,
        root: str | Path,
    ) -> list[IndexedFile]:

        root = Path(root)

        index = []

        for file in root.rglob("*"):

            if not file.is_file():
                continue

            language = self.EXTENSIONS.get(
                file.suffix.lower()
            )

            if language is None:
                continue

            try:

                content = file.read_bytes()

            except Exception:
                continue

            index.append(

                IndexedFile(

                    path=str(
                        file.relative_to(root)
                    ).replace("\\","/"),

                    language=language,

                    lines=content.count(b"\n")+1,

                    size=len(content),

                    sha256=hashlib.sha256(
                        content
                    ).hexdigest(),

                )

            )

        return index


project_indexer = ProjectIndexer()
