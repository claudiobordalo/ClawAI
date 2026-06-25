from __future__ import annotations

import ast
import json
from pathlib import Path


class SymbolIndexer:

    CACHE = ".clawai/symbol_index.json"

    def build(
        self,
        project: str | Path,
    ) -> dict[str, str]:

        root = Path(project)

        cache = root / self.CACHE

        cache.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        index = {}

        ignored = {
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
        }

        for file in root.rglob("*.py"):

            if any(
                part in ignored
                for part in file.parts
            ):
                continue

            try:

                tree = ast.parse(
                    file.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                )

            except Exception:
                continue

            relative = str(
                file.relative_to(root)
            )

            for node in ast.walk(tree):

                if isinstance(
                    node,
                    (
                        ast.ClassDef,
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):

                    index[node.name.lower()] = relative

        cache.write_text(
            json.dumps(
                index,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return index

    def load(
        self,
        project: str | Path,
    ) -> dict[str, str]:

        root = Path(project)

        cache = root / self.CACHE

        if cache.exists():

            return json.loads(
                cache.read_text(
                    encoding="utf-8",
                )
            )

        return self.build(project)
