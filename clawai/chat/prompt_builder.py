from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clawai.ai.router import ModelRole
from clawai.documents.reader import documents
from clawai.workspaces.manager import workspace_manager


@dataclass(slots=True, frozen=True)
class PreparedPrompt:
    text: str
    role: ModelRole = ModelRole.DEFAULT
    used_workspace_context: bool = False
    used_file_context: bool = False


class PromptBuilder:
    def __init__(
        self,
        *,
        max_prompt_chars: int = 8_000,
        max_workspace_items: int = 30,
        max_excerpt_lines: int = 80,
        max_excerpt_chars: int = 4_000,
    ) -> None:
        self.max_prompt_chars = max_prompt_chars
        self.max_workspace_items = max_workspace_items
        self.max_excerpt_lines = max_excerpt_lines
        self.max_excerpt_chars = max_excerpt_chars

    def build(self, prompt: str, file: str | None = None) -> PreparedPrompt:
        parts: list[str] = []
        role = ModelRole.DEFAULT
        used_workspace_context = False
        used_file_context = False

        if file:
            path = Path(file)
            suffix = path.suffix.lower()
            if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}:
                role = ModelRole.VISION
                parts.append(f"Arquivo de imagem enviado: {path.name}")
                parts.append(f"Caminho: {path}")
            else:
                file_text = self._read_file_text(path)
                if file_text:
                    used_file_context = True
                    parts.append(f"Arquivo enviado: {path.name}")
                    parts.append("Conteúdo do arquivo:")
                    parts.append(self._clip_text(file_text, self.max_excerpt_chars))
                else:
                    parts.append(f"Arquivo enviado: {path.name}")
                    parts.append(f"Caminho: {path}")

        workspace_context = self._build_workspace_context(prompt)
        if workspace_context:
            used_workspace_context = True
            parts.append("Contexto do workspace:")
            parts.append(workspace_context)

        parts.append("Pergunta do usuário:")
        parts.append(prompt)

        prepared = "\n\n".join(parts).strip()
        prepared = self._clip_text(prepared, self.max_prompt_chars)

        return PreparedPrompt(
            text=prepared,
            role=role,
            used_workspace_context=used_workspace_context,
            used_file_context=used_file_context,
        )

    def _build_workspace_context(self, prompt: str) -> str | None:
        prompt_lower = (prompt or "").lower().strip()
        if not prompt_lower:
            return None

        workspace_hints = (
            "workspace",
            "projeto",
            "arquivo",
            "arquivos",
            "estrutura",
            "arquitetura",
            "repo",
            "repositório",
            "refatore",
            "corrija",
            "implemente",
            "analise",
            "explore",
            "pesquise",
        )
        if not any(hint in prompt_lower for hint in workspace_hints):
            return None

        try:
            workspace = workspace_manager.current()
        except Exception:
            return None

        root = Path(getattr(workspace, "root", "")).expanduser().resolve()
        if not root.exists():
            return None

        target = self._resolve_workspace_target(prompt_lower, root)
        if target is not None:
            rel_path = self._relative_to_root(target, root)
            if target.is_dir():
                tree = self._build_tree_summary(
                    target,
                    workspace_id=getattr(workspace, "workspace_id", None),
                    max_items=self.max_workspace_items,
                )
                return (
                    f"Workspace ativo: {getattr(workspace, 'name', root.name)}\n"
                    f"Caminho: {root}\n"
                    f"Pasta relevante: {rel_path}\n\n"
                    f"Árvore resumida:\n{tree}"
                )

            if target.is_file():
                excerpt = self._safe_file_excerpt(
                    target,
                    max_lines=self.max_excerpt_lines,
                    max_chars=self.max_excerpt_chars,
                )
                if excerpt:
                    return (
                        f"Workspace ativo: {getattr(workspace, 'name', root.name)}\n"
                        f"Caminho: {root}\n"
                        f"Arquivo relevante: {rel_path}\n\n"
                        f"Conteúdo:\n{excerpt}"
                    )

        tree = self._build_tree_summary(
            root,
            workspace_id=getattr(workspace, "workspace_id", None),
            max_items=self.max_workspace_items,
        )
        return (
            f"Workspace ativo: {getattr(workspace, 'name', root.name)}\n"
            f"Caminho: {root}\n\n"
            f"Árvore resumida:\n{tree}"
        )

    def _build_tree_summary(self, root: Path, *, workspace_id: str | None = None, max_items: int = 30) -> str:
        try:
            current_root = Path(workspace_manager.current().root).expanduser().resolve()
            relative = ""
            if root != current_root:
                relative = self._relative_to_root(root, current_root)
            items = workspace_manager.tree(relative, workspace_id=workspace_id)
        except Exception:
            items = []

        if items:
            lines: list[str] = []
            for item in items[:max_items]:
                marker = "/" if item.get("directory") else ""
                lines.append(f"- {item.get('name', '')}{marker}")
            if len(items) > max_items:
                lines.append(f"- ... (+{len(items) - max_items} itens)")
            return "\n".join(lines) or "(vazio)"

        lines: list[str] = []
        try:
            for child in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if child.name.startswith("."):
                    continue
                if child.name in {
                    "__pycache__",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".ruff_cache",
                    ".venv",
                    "node_modules",
                }:
                    continue
                marker = "/" if child.is_dir() else ""
                lines.append(f"- {child.name}{marker}")
                if len(lines) >= max_items:
                    break
        except Exception:
            return "(vazio)"

        return "\n".join(lines) or "(vazio)"

    def _resolve_workspace_target(self, prompt_lower: str, root: Path) -> Path | None:
        if not prompt_lower:
            return None

        stopwords = {
            "o",
            "a",
            "os",
            "as",
            "um",
            "uma",
            "de",
            "do",
            "da",
            "dos",
            "das",
            "que",
            "como",
            "funciona",
            "existe",
            "nesse",
            "nesa",
            "nesse",
            "projeto",
            "workspace",
            "arquivo",
            "arquivos",
            "frontend",
            "backend",
            "api",
            "app",
            "analise",
            "analisar",
            "explore",
            "pesquise",
        }

        tokens = self._tokenize_pathlike(prompt_lower)
        for token in tokens:
            if token in stopwords:
                continue
            candidate = root / token
            if candidate.exists():
                return candidate

        if "frontend" in prompt_lower:
            candidate = root / "frontend"
            if candidate.exists():
                return candidate

        if prompt_lower.startswith("analise "):
            remainder = prompt_lower[len("analise "):].strip()
            token = remainder.split()[0] if remainder else ""
            if token:
                candidate = root / token
                if candidate.exists() or candidate.suffix:
                    return candidate

        return None

    def _tokenize_pathlike(self, text: str) -> list[str]:
        import re

        return re.findall(r"[A-Za-z0-9._/-]+", text)

    def _safe_file_excerpt(self, path: Path, *, max_lines: int, max_chars: int) -> str | None:
        try:
            content = self._read_file_text(path)
        except Exception:
            return None
        if not content:
            return None

        lines = content.splitlines()[:max_lines]
        excerpt = "\n".join(lines)
        return self._clip_text(excerpt, max_chars)

    def _read_file_text(self, path: Path) -> str | None:
        try:
            return documents.read(path)
        except Exception:
            try:
                return path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return None

    def _relative_to_root(self, path: Path, root: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except Exception:
            return path.as_posix()

    def _clip_text(self, text: str, limit: int) -> str:
        text = (text or "").strip()
        if len(text) <= limit:
            return text
        return text[:limit] + "\n..."