from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fnmatch


@dataclass(frozen=True, slots=True)
class IgnoreRules:
    patterns: tuple[str, ...]
    root: Path
    # If True, ignore everything under a matching pattern
    negated: tuple[bool, ...]


class IgnoreEngine:
    """
    IgnoreEngine:
    - Interpreta .gitignore (subset)
    - Aplica regras internas obrigatórias
    - Ignora binários
    """

    INTERNAL_PATH_PREFIXES = (
        "node_modules",
        ".venv",
        "dist",
        "build",
    )

    INTERNAL_FILES = (
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
    )

    def __init__(
        self,
        root: str | Path,
    ) -> None:
        self.root = Path(root)
        self._gitignore_patterns: list[str] = []
        self._negated_flags: list[bool] = []

    def load(self) -> None:
        gitignore = self._find_gitignore(self.root)
        if gitignore is None:
            self._gitignore_patterns = []
            self._negated_flags = []
            return

        patterns: list[str] = []
        negated: list[bool] = []

        for raw in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            is_neg = line.startswith("!")
            if is_neg:
                line = line[1:].strip()
                if not line:
                    continue

            patterns.append(line)
            negated.append(is_neg)

        self._gitignore_patterns = patterns
        self._negated_flags = negated

    def _find_gitignore(self, root: Path) -> Path | None:
        # Projeto único: usamos o .gitignore do root (mais previsível)
        candidate = root / ".gitignore"
        if candidate.exists() and candidate.is_file():
            return candidate
        return None

    def is_ignored(
        self,
        path: str | Path,
        *,
        is_dir: bool = False,
        is_binary: bool = False,
    ) -> bool:
        p = Path(path)

        try:
            rel = p.relative_to(self.root)
        except Exception:
            rel = p

        rel_str = str(rel).replace("\\", "/")

        # Regra interna: binários
        if is_binary:
            return True

        # Regra interna: diretórios/arquivos específicos
        parts = rel.parts
        if any(part in self.INTERNAL_FILES for part in parts):
            return True

        for prefix in self.INTERNAL_PATH_PREFIXES:
            if rel_str == prefix or rel_str.startswith(prefix + "/"):
                return True

        # Regras internas: pycache/explicitamente
        if "__pycache__" in parts:
            return True

        # .gitignore (subset): implementa:
        # - padrões sem / aplicam por basename
        # - padrões com / aplicam por path relativo ("/" normalizado)
        # - suficiência com trailing "/" trata como diretório
        #
        # Observação: comportamento aproximado, suficiente para testes unitários.
        matched = False
        result = False

        for pat, is_neg in zip(self._gitignore_patterns, self._negated_flags):
            if pat.endswith("/"):
                # diretório
                pat2 = pat[:-1]
                if is_dir:
                    if self._match_dir(rel_str, pat2):
                        matched = True
                        result = not is_neg
                continue

            # normalização
            if "/" not in pat:
                # basename
                if fnmatch.fnmatch(p.name, pat):
                    matched = True
                    result = not is_neg
            else:
                if fnmatch.fnmatch(rel_str, pat) or fnmatch.fnmatch(rel_str, pat.lstrip("./")):
                    matched = True
                    result = not is_neg

        if matched:
            return result

        return False

    def _match_dir(self, rel_str: str, pat: str) -> bool:
        # "foo/" deve ignorar foo/... e foo
        if rel_str == pat:
            return True
        return rel_str.startswith(pat + "/")

    def ignore_many(
        self,
        paths: Iterable[Path],
        *,
        is_binary_lookup: callable | None = None,
    ) -> dict[Path, bool]:
        out: dict[Path, bool] = {}
        for p in paths:
            is_dir = p.is_dir()
            is_bin = False
            if is_binary_lookup is not None:
                is_bin = bool(is_binary_lookup(p))
            out[p] = self.is_ignored(p, is_dir=is_dir, is_binary=is_bin)
        return out


def is_probably_binary(path: str | Path) -> bool:
    """
    Heurística: lê apenas um pequeno prefixo e detecta bytes nulos.
    """
    p = Path(path)
    try:
        with p.open("rb") as f:
            chunk = f.read(8192)
    except Exception:
        return False
    if not chunk:
        return False
    if b"\x00" in chunk:
        return True
    # Se tiver muita "não-utf8" provável, consideramos binário.
    textish = 0
    for b in chunk:
        if 9 <= b <= 13 or 32 <= b <= 126:
            textish += 1
    return textish / max(1, len(chunk)) < 0.85
