from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ProjectNode:
    """
    Representação leve da árvore do projeto.
    Contém apenas nomes e relações (sem conteúdo e sem carregar arquivo).
    """

    name: str
    is_dir: bool
    children: tuple["ProjectNode", ...] = ()

    def iter_files(self) -> Iterable["ProjectNode"]:
        if not self.is_dir:
            yield self
            return
        for c in self.children:
            yield from c.iter_files()


@dataclass(frozen=True, slots=True)
class ProjectTree:
    root: Path
    root_node: ProjectNode

    def iter_files(self) -> Iterable[ProjectNode]:
        return self.root_node.iter_files()
