from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ignore import IgnoreEngine


@dataclass(frozen=True, slots=True)
class ScanEntry:
    path: Path
    is_dir: bool


class Scanner:
    """
    Scanner:
    - lista diretórios e arquivos (descoberta)
    - respeita IgnoreEngine
    - não lê conteúdo
    """

    def __init__(
        self,
        root: str | Path,
        ignore_engine: IgnoreEngine | None = None,
    ) -> None:
        self.root = Path(root)
        self.ignore = ignore_engine or IgnoreEngine(self.root)
        self.ignore.load()

    def list_directories(self) -> list[Path]:
        out: list[Path] = []
        for p in self.root.iterdir():
            if p.name.startswith("."):
                continue
            if p.is_dir() and not self.ignore.is_ignored(p, is_dir=True):
                out.append(p)
        return out

    def list_files(self, *, max_files: int | None = None) -> list[Path]:
        out: list[Path] = []

        # Descoberta recursiva, mas apenas para arquivos "indexáveis".
        for p in self.root.rglob("*"):
            if not p.is_file():
                continue

            if p.name.startswith("."):
                continue

            if self.ignore.is_ignored(p, is_dir=False):
                continue

            out.append(p)

            if max_files is not None and len(out) >= max_files:
                break

        return out
