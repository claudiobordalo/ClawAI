from __future__ import annotations

import ast
from pathlib import Path

from clawai.workspace.models.indexed_file import IndexedFile


class ProjectIndexer:

    def index_file(
        self,
        file: Path,
    ) -> IndexedFile:

        indexed = IndexedFile(
            path=file,
            language="Python",
            size=file.stat().st_size,
        )

        tree = ast.parse(
            file.read_text(
                encoding="utf-8",
            )
        )

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):
                indexed.imports.extend(
                    alias.name
                    for alias in node.names
                )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""

                indexed.imports.append(module)

            elif isinstance(node, ast.ClassDef):
                indexed.classes.append(node.name)

            elif isinstance(node, ast.FunctionDef):
                indexed.functions.append(node.name)

        return indexed
