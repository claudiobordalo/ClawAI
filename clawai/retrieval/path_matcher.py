from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Match:
    path: str
    score: int
    rule: str
    base_len: int
    ext_rank: int


class PathMatcher:
    """
    Realiza correspondência simples determinística entre caminhos e um texto livre.
    Regras de ranking: equality > prefix/suffix > contains.
    Tie-break: caminho em ordem lexicográfica.
    """

    def match(self, files: Iterable[str], query: str) -> Tuple[str, ...]:
        q = (query or "").strip().lower()
        if not q:
            return tuple(sorted(set(files)))

        matches: list[Match] = []
        for f in files:
            p = f.lower()
            base = p.split("/")[-1]
            score = 0
            rule = ""
            if p == q or p.endswith("/" + q):
                score = 100
                rule = "equality"
            elif base.startswith(q) or p.startswith(q):
                score = 80
                rule = "prefix"
            elif base.endswith(q) or p.endswith(q):
                score = 70
                rule = "suffix"
            elif q in p:
                score = 50
                rule = "contains"

            if score > 0:
                ext = base.split(".")[-1] if "." in base else ""
                ext_rank = 0 if ext == "py" else 1
                matches.append(Match(path=f, score=score, rule=rule, base_len=len(base), ext_rank=ext_rank))

        matches.sort(key=lambda m: (-m.score, m.ext_rank, m.base_len, -len(m.path), m.path))
        return tuple(m.path for m in matches)
