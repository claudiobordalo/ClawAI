from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from clawai.codebase import ProjectSnapshot

from .path_matcher import PathMatcher
from .symbol_index import SymbolIndex, SymbolRef


@dataclass(frozen=True)
class RetrievalResult:
    files: Tuple[str, ...]
    symbols: Tuple[SymbolRef, ...]
    score: int
    reason: str


class ContextRetriever:
    """
    Integra PathMatcher e SymbolIndex para retornar contexto relevante determinístico.
    """

    def __init__(self, *, matcher: PathMatcher | None = None) -> None:
        self._matcher = matcher or PathMatcher()

    def retrieve(self, snapshot: ProjectSnapshot, query: str) -> RetrievalResult:
        root = Path(snapshot.root)
        # Lista de arquivos relativos do snapshot
        rel_files = tuple(str(Path(f.path).resolve().relative_to(root)).replace("\\", "/") for f in snapshot.files)

        # Path match
        file_candidates = self._matcher.match(rel_files, query)

        # Symbol match
        index = SymbolIndex(snapshot)
        sym_matches: tuple[SymbolRef, ...] = ()
        q = (query or "").strip()
        if q:
            # Tenta encontrar símbolo por nome simples (case sensitive)
            # Primeiro tenta igual; caso vazio, tenta case-insensitive
            res = index.find_symbol(q)
            if not res:
                res = index.find_symbol(q.strip())
            sym_matches = res

        # Scoring simples: número de matches ponderado
        score = 0
        reason_parts: list[str] = []
        if file_candidates:
            score += 10 * len(file_candidates[:5])
            reason_parts.append(f"{len(file_candidates)} file matches")
        if sym_matches:
            score += 20 * len(sym_matches[:5])
            reason_parts.append(f"{len(sym_matches)} symbol matches")
        if not reason_parts:
            reason_parts.append("no matches")

        reason = "; ".join(reason_parts)
        return RetrievalResult(files=file_candidates, symbols=sym_matches, score=score, reason=reason)
