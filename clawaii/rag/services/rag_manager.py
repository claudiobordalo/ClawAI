from __future__ import annotations

from pathlib import Path

from clawai.rag.models.context_document import ContextDocument


class RAGManager:

    def load_project(
        self,
        root: str | Path,
    ) -> list[ContextDocument]:

        root = Path(root)

        documents: list[ContextDocument] = []

        ignored = {
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
            ".idea",
            ".vscode"
        }

        for file in root.rglob("*"):

            if not file.is_file():
                continue

            if any(
                part in ignored
                for part in file.parts
            ):
                continue

            try:

                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

            except Exception:
                continue

            documents.append(
                ContextDocument(
                    path=file,
                    content=content,
                )
            )

        return documents
