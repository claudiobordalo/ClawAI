from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .project_snapshot import ModuleInfo


@dataclass(frozen=True)
class ModuleDependencies:
    file: str
    defined_symbols: Tuple[str, ...] = ()
    imports: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DependencyGraph:
    modules: Tuple[ModuleDependencies, ...] = ()

    @staticmethod
    def build(modules: Tuple[ModuleInfo, ...]) -> "DependencyGraph":
        nodes: list[ModuleDependencies] = []
        for m in modules:
            defined: list[str] = []
            defined.extend(fn.name for fn in m.functions)
            defined.extend(cls.name for cls in m.classes)
            nodes.append(
                ModuleDependencies(
                    file=m.file.path,
                    defined_symbols=tuple(defined),
                    imports=m.imports,
                )
            )
        return DependencyGraph(modules=tuple(nodes))
