from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .file_scanner import FileScanner
from .symbol_extractor import SymbolExtractor
from .dependency_graph import DependencyGraph
from .project_snapshot import ProjectSnapshot, SourceFile, ModuleInfo


class CodeAnalyzer:
    """
    Classe principal de análise estática.
    Fluxo: FileScanner -> SymbolExtractor -> DependencyGraph -> ProjectSnapshot
    """

    def __init__(self, *, file_scanner: FileScanner | None = None, symbol_extractor: SymbolExtractor | None = None) -> None:
        self._scanner = file_scanner or FileScanner()
        self._extractor = symbol_extractor or SymbolExtractor()

    def analyze(self, root: str | Path, *, exts: Sequence[str] | None = None) -> ProjectSnapshot:
        root_path = Path(root).resolve()
        files = self._scanner.scan(root_path, exts=exts)

        # Monta SourceFiles
        source_files = tuple(
            SourceFile(path=str(root_path.joinpath(rel)), extension=Path(rel).suffix)
            for rel in files
        )

        # Extrai módulos apenas para .py (ignora __init__.py nesta sprint)
        module_infos: list[ModuleInfo] = []
        for sf in source_files:
            if sf.extension == ".py" and Path(sf.path).name != "__init__.py":
                module_infos.append(self._extractor.extract(sf.path))
        modules_tuple = tuple(module_infos)

        graph = DependencyGraph.build(modules_tuple)

        return ProjectSnapshot(
            root=str(root_path),
            files=source_files,
            modules=modules_tuple,
            dependency_graph=graph,
        )
