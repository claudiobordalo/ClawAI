from __future__ import annotations

import ast
from pathlib import Path


class CodeExtractor:

    def extract(
        self,
        file: str | Path,
        symbol: str,
    ) -> str:

        file = Path(file)

        source = file.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        tree = ast.parse(source)

        lines = source.splitlines()

        for node in ast.walk(tree):

            if not isinstance(
                node,
                (
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                continue

            if node.name.lower() != symbol.lower():
                continue

            start = node.lineno - 1

            end = getattr(
                node,
                "end_lineno",
                start + 80,
            )

            return "\n".join(
                lines[start:end]
            )

        return source[:1000]
