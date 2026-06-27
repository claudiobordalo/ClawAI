from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, Tuple

_DEFAULT_EXTS = (".py", ".md", ".toml", ".yaml", ".yml", ".json")
_IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    ".env",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "node_modules",
}


class FileScanner:
    """
    Responsável por localizar arquivos relevantes do projeto, sem ler conteúdo.
    - Percorre diretórios recursivamente.
    - Ignora diretórios padrão.
    - Suporta filtros por extensão.
    - Retorna coleção determinística (ordenada) de caminhos relativos ao root.
    """

    def scan(self, root: str | Path, exts: Sequence[str] | None = None) -> Tuple[str, ...]:
        root_path = Path(root).resolve()
        allowed_exts = tuple(exts) if exts is not None else _DEFAULT_EXTS

        results: list[str] = []
        for path in root_path.rglob("*"):
            if not path.is_file():
                continue
            # Skip ignored directories
            if any(part in _IGNORED_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in allowed_exts:
                rel = str(path.relative_to(root_path)).replace("\\", "/")
                results.append(rel)

        results.sort()
        return tuple(results)
