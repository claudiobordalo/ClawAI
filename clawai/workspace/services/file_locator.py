from __future__ import annotations

import re
from pathlib import Path

from .symbol_indexer import SymbolIndexer


class FileLocator:

    def find(
        self,
        project: str | Path,
        question: str,
        limit: int = 3,
    ) -> list[Path]:

        root = Path(project)

        symbols = SymbolIndexer().load(project)

        found = []

        names = re.findall(
            r"[A-Z][A-Za-z0-9_]+",
            question,
        )

        if not names:
            names = re.findall(
                r"[A-Za-z_][A-Za-z0-9_]*",
                question,
            )

        for name in names:

            path = symbols.get(
                name.lower()
            )

            if not path:
                continue

            file = root / path

            if file not in found:
                found.append(file)

        return found[:limit]
