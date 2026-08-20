from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class SourceFile:
    path: str
    extension: str


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    decorators: Tuple[str, ...] = ()
    docstring: str | None = None
    is_method: bool = False


@dataclass(frozen=True)
class ClassInfo:
    name: str
    bases: Tuple[str, ...] = ()
    methods: Tuple[FunctionInfo, ...] = ()
    decorators: Tuple[str, ...] = ()
    docstring: str | None = None


@dataclass(frozen=True)
class ModuleInfo:
    file: SourceFile
    module_name: str
    imports: Tuple[str, ...] = ()
    classes: Tuple[ClassInfo, ...] = ()
    functions: Tuple[FunctionInfo, ...] = ()
    docstring: str | None = None
    parse_error: str | None = None


@dataclass(frozen=True)
class ProjectSnapshot:
    root: str
    files: Tuple[SourceFile, ...] = ()
    modules: Tuple[ModuleInfo, ...] = ()
    dependency_graph: object | None = None
