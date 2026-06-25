from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from clawai.workspace.file_reader import FileReader
from clawai.workspace.ignore import IgnoreEngine
from clawai.workspace.project_tree import ProjectTree
from clawai.workspace.scanner import Scanner


@dataclass(frozen=True, slots=True)
class ContextCandidate:
    path: Path
    score: int
    reason: str


@dataclass(frozen=True, slots=True)
class ContextResult:
    context: str
    selected_files: list[str]


@dataclass(frozen=True, slots=True)
class IncrementalContextResult:
    context: str
    selected_files: list[str]


class ContextBuilder:
    """
    ContextBuilder incremental e inteligente.

    Fluxo (no método build):
    1) Analisar objetivo
    2) Selecionar somente diretórios relevantes
    3) Listar apenas arquivos desses diretórios (via Scanner)
    4) Classificar por relevância (heurística)
    5) Ler apenas arquivos necessários (via FileReader)
    6) Parar quando atingir max_chars

    Heurísticas são extensíveis via _TOPIC_PRIORITIES.
    """

    DEFAULT_EXTENSIONS = {".py", ".md", ".toml", ".json", ".yaml", ".yml", ".txt", ".pdf"}

    # Tópicos facilmente extensíveis: cada tópico tem palavras-chave e boost.
    _TOPIC_PRIORITIES: dict[str, dict[str, object]] = {
        "pdf": {"keywords": ["pdf", "document", "reader", "parser", "ocr"], "boost": 8, "ext": [".pdf"]},
        "git": {"keywords": ["git", "repository", "composio", "github"], "boost": 7, "ext": [".git"]},
        "dofus": {"keywords": ["dofus", "game", "bot", "automation"], "boost": 7, "ext": []},
        "patch": {"keywords": ["patch", "replace", "operations", "context"], "boost": 6, "ext": []},
    }

    def __init__(self, *, extensions: set[str] | None = None) -> None:
        self._extensions = extensions or set(self.DEFAULT_EXTENSIONS)

    # -------------------------
    # NOVA API (build)
    # -------------------------
    def build(
        self,
        *,
        objective: str,
        project_tree: ProjectTree,
        scanner: Scanner,
        file_reader: FileReader,
        max_chars: int = 120_000,
        max_candidates: int = 50,
        max_files: int = 25,
        file_is_allowed: Callable[[Path], bool] | None = None,
    ) -> ContextResult:
        objective_l = objective.lower()

        # 1) analisar objetivo
        tokens = self._tokenize(objective_l)
        topics = self._detect_topics(objective_l)

        # 2) selecionar somente diretórios relevantes (somente no nível imediato do root)
        relevant_dir_names = self._select_relevant_dir_names(project_tree, objective_l=objective_l, tokens=tokens)

        # 3) listar apenas arquivos desses diretórios
        files = scanner.list_files()

        filtered: list[Path] = []
        for f in files:
            try:
                rel_parts = f.relative_to(project_tree.root).parts
            except Exception:
                rel_parts = Path(str(f)).parts
            if any(part in relevant_dir_names for part in rel_parts):
                # extensão indexável
                if f.suffix.lower() in self._extensions:
                    filtered.append(f)

        # 4) classificar arquivos por relevância
        candidates = self._rank_candidates(
            files=filtered,
            objective_l=objective_l,
            tokens=tokens,
            topics=topics,
            max_candidates=max_candidates,
        )

        # 5) ler apenas os arquivos necessários (sob demanda)
        used = 0
        blocks: list[str] = []
        selected: list[str] = []

        allow = file_is_allowed or (lambda _p: True)

        for cand in candidates[:max_files]:
            if not allow(cand.path):
                continue

            remaining = max_chars - used
            if remaining <= 0:
                break

            content = file_reader.read_text(cand.path, max_chars=remaining)
            if not content:
                continue

            rel = str(cand.path.relative_to(project_tree.root)).replace("\\", "/")

            block = (
                "\n==============================\n"
                f"Arquivo: {rel}\n"
                "==============================\n\n"
                f"{content}\n"
            )

            if used + len(block) > max_chars:
                blocks.append(block[:remaining])
                used += remaining
                selected.append(rel)
                break

            blocks.append(block)
            used += len(block)
            selected.append(rel)

        return ContextResult(context="\n".join(blocks), selected_files=selected)

    # -------------------------
    # Compatibilidade: API antiga incremental_build
    # -------------------------
    def incremental_build(
        self,
        project: str | Path,
        objective: str,
        *,
        max_files: int = 25,
        max_chars: int = 120_000,
    ) -> IncrementalContextResult:
        """
        Mantém comportamento compatível com os testes existentes:
        - heurística por tokens em nomes de diretórios/arquivos
        - lê somente arquivos selecionados (sob demanda)
        """
        root = Path(project)

        # listar apenas itens de 1 nível (compat)
        root_items = [p for p in root.iterdir() if not p.name.startswith(".")]

        objective_tokens = self._tokenize(objective)

        folder_candidates = self._select_relevant_folders_compat(
            root_items=root_items,
            objective_tokens=objective_tokens,
        )

        files = self._list_files_in_folders_compat(
            root=root,
            folder_paths=folder_candidates,
        )

        selected = self._select_relevant_files_compat(
            files=files,
            objective_tokens=objective_tokens,
            max_files=max_files,
        )

        context = self._build_context_from_files_compat(
            root=root,
            selected=selected,
            max_chars=max_chars,
        )

        return IncrementalContextResult(
            context=context,
            selected_files=[str(p.relative_to(root)).replace("\\", "/") for p in selected],
        )

    def _select_relevant_folders_compat(
        self,
        *,
        root_items: Iterable[Path],
        objective_tokens: list[str],
    ) -> list[Path]:
        folders = [p for p in root_items if p.is_dir()]

        if not objective_tokens:
            return [p for p in folders if p.name in {"clawai", "core", "workspace", "agents", "ai", "prompts", "tests"}] or folders[:6]

        matched: list[tuple[int, Path]] = []
        for folder in folders:
            score = 0
            folder_name = folder.name.lower()

            for token in objective_tokens:
                if token in folder_name:
                    score += 3

                # palavras-chave por pasta (heurística)
                for _, aliases in self.DEFAULT_FOLDER_KEYWORDS.items():
                    if folder_name in aliases:
                        score += 1

            if any(k in folder_name for k in self.DEFAULT_FOLDER_KEYWORDS.keys()):
                score += 1

            if score > 0:
                matched.append((score, folder))

        matched.sort(key=lambda x: x[0], reverse=True)
        top = [p for _, p in matched[:10]]

        if not top:
            preferred = ["clawai", "core", "workspace", "agents", "ai", "prompts", "providers", "tools", "tests", "projects"]
            top = [p for p in folders if p.name in preferred]

        return top or folders[:6]

    # Reaproveita heurísticas originais (mantidas aqui só para compat)
    DEFAULT_FOLDER_KEYWORDS = {
        "agent": ["agents", "agent"],
        "agents": ["agents"],
        "router": ["ai", "router"],
        "prompt": ["prompts", "prompt"],
        "workspace": ["workspace"],
        "tools": ["tools"],
        "tests": ["tests"],
        "core": ["core"],
        "providers": ["providers"],
        "application": ["application"],
        "orchestrator": ["orchestrator"],
        "rag": ["rag"],
        "memory": ["memory"],
        "indexing": ["indexing", "index"],
        "projects": ["projects"],
        "docs": ["docs"],
        "api": ["api"],
    }

    def _list_files_in_folders_compat(
        self,
        *,
        root: Path,
        folder_paths: list[Path],
    ) -> list[Path]:
        ignored_parts = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}

        files: list[Path] = []
        for folder in folder_paths:
            for f in folder.rglob("*"):
                if not f.is_file():
                    continue
                if any(part in ignored_parts for part in f.parts):
                    continue
                if f.suffix.lower() not in self._extensions:
                    continue
                files.append(f)
        return files

    def _select_relevant_files_compat(
        self,
        *,
        files: list[Path],
        objective_tokens: list[str],
        max_files: int,
    ) -> list[Path]:
        if not files:
            return []

        def score_for(p: Path) -> int:
            s = 0
            rel = str(p).lower()

            for t in objective_tokens:
                if t in rel:
                    s += 5

            name = p.name.lower()
            if name in {"readme.md", "main.py"}:
                s += 2

            if p.suffix.lower() in {".py", ".md", ".toml", ".json"}:
                s += 1

            return s

        ranked = sorted(files, key=score_for, reverse=True)
        if objective_tokens and all(score_for(p) == 0 for p in ranked[: min(10, len(ranked))]):
            ranked = files

        return ranked[:max_files]

    def _build_context_from_files_compat(
        self,
        *,
        root: Path,
        selected: list[Path],
        max_chars: int,
    ) -> str:
        context_blocks: list[str] = []
        used = 0

        for f in selected:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            rel = str(f.relative_to(root)).replace("\\", "/")

            block = (
                "\n==============================\n"
                f"Arquivo: {rel}\n"
                "==============================\n\n"
                f"{content}\n"
            )

            if used >= max_chars:
                break

            remaining = max_chars - used
            if len(block) > remaining:
                context_blocks.append(block[:remaining])
                used += remaining
                break

            context_blocks.append(block)
            used += len(block)

        return "\n".join(context_blocks)

    # -------------------------
    # Heurísticas
    # -------------------------
    def _tokenize(self, text: str) -> list[str]:
        tokens: list[str] = []
        current: list[str] = []
        for ch in text:
            if ch.isalnum() or ch == "_":
                current.append(ch)
            else:
                if current:
                    tokens.append("".join(current))
                    current = []
        if current:
            tokens.append("".join(current))

        seen = set()
        out: list[str] = []
        for t in tokens:
            if t in seen:
                continue
            seen.add(t)
            if len(t) < 2:
                continue
            out.append(t)
        return out

    def _detect_topics(self, objective_l: str) -> set[str]:
        hits: set[str] = set()
        for topic, cfg in self._TOPIC_PRIORITIES.items():
            for kw in cfg.get("keywords", []):  # type: ignore[union-attr]
                if kw in objective_l:
                    hits.add(topic)
        return hits

    def _select_relevant_dir_names(
        self,
        project_tree: ProjectTree,
        *,
        objective_l: str,
        tokens: list[str],
    ) -> set[str]:
        """
        Heurística simples e extensível:
        - quando objetivo contém tópicos (ex: PDF), retorna apenas dirs que combinam fortemente
          com palavras-chave/tokens desses tópicos.
        - fallback só quando nada casar (para não “vazar” diretórios irrelevantes).
        - restringe ao 1º nível (imediato) do root_node
        """
        root_children = list(project_tree.root_node.children)
        dir_names = [c.name for c in root_children if c.is_dir]

        if not dir_names:
            return set(tokens[:8]) if tokens else {"agents", "core", "workspace", "tools", "tests", "docs"}

        # 1) match forte por tópicos (prioriza o que o objetivo explicitamente pede)
        topic_dir_scores: dict[str, int] = {d: 0 for d in dir_names}
        for topic, cfg in self._TOPIC_PRIORITIES.items():
            keywords = list(cfg.get("keywords", []))  # type: ignore[arg-type]
            boost = int(cfg.get("boost", 0))

            if any(kw in objective_l for kw in keywords):
                for d in dir_names:
                    dl = d.lower()
                    if any(kw in dl for kw in keywords):
                        topic_dir_scores[d] += boost

        best_topic = [d for d, s in topic_dir_scores.items() if s > 0]
        if best_topic:
            return set(best_topic)

        # 2) match por tokens do objetivo (match parcial)
        token_matches: set[str] = set()
        for d in dir_names:
            dl = d.lower()
            if any(t in dl for t in tokens):
                token_matches.add(d)

        if token_matches:
            # limita para manter contexto pequeno, mas sem incluir irrelevantes
            ranked = sorted(token_matches, key=lambda n: len(n), reverse=True)
            return set(ranked[:6])

        # 3) fallback mínimo
        preferred = {"agents", "core", "workspace", "tools", "tests", "docs"}
        preferred_matches = [d for d in dir_names if d in preferred]
        if preferred_matches:
            return set(preferred_matches[:6])

        # último recurso: usa até 1-2 diretórios (evita explodir leitura)
        return set(dir_names[:2])

    def _rank_candidates(
        self,
        *,
        files: list[Path],
        objective_l: str,
        tokens: list[str],
        topics: set[str],
        max_candidates: int,
    ) -> list[ContextCandidate]:
        def score_path(p: Path) -> tuple[int, str]:
            rel = str(p).lower()
            score = 0
            reasons: list[str] = []

            # boosts por topics
            for topic in topics:
                cfg = self._TOPIC_PRIORITIES.get(topic)
                if not cfg:
                    continue
                boost = int(cfg.get("boost", 0))
                keywords = cfg.get("keywords", [])
                if any(kw in objective_l for kw in keywords):  # topic detectado
                    if any(kw in rel for kw in keywords):
                        score += boost
                        reasons.append(f"topic:{topic}")

            # match token em path
            for t in tokens:
                if t in rel:
                    score += 5
                    reasons.append(f"token:{t}")

            # extensões relevantes
            if p.suffix.lower() in self._extensions:
                score += 1

            name = p.name.lower()
            if name in {"readme.md", "main.py"}:
                score += 2
                reasons.append("corefile")

            reason = ",".join(dict.fromkeys(reasons)) or "default"
            return score, reason

        ranked = []
        for f in files:
            s, r = score_path(f)
            ranked.append(ContextCandidate(path=f, score=s, reason=r))

        ranked.sort(key=lambda c: (c.score, c.reason), reverse=True)
        # ainda assim mantém ordem determinística por path quando scores iguais
        ranked.sort(key=lambda c: (c.score, str(c.path)), reverse=True)

        return ranked[:max_candidates]


context_builder = ContextBuilder()

