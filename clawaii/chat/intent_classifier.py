from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from clawai.ai.router import ModelRole

VISION_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
}

ENGINEERING_HINTS = (
    "implemente",
    "corrija",
    "refatore",
    "ajuste",
    "analise",
    "investigue",
    "workspace",
    "projeto",
    "arquivo",
    "arquivos",
    "git",
    "teste",
    "tool",
    "provider",
    "composio",
    "mcp",
    "patch",
    "terminal",
    "editor",
    "search",
    "build",
    "deploy",
    "erro",
    "bug",
    "falha",
    "acessar",
    "abrir",
    "listar",
    "verificar",
    "mostrar",
    "conteúdo",
    "conteudo",
)

WORKSPACE_HINTS = (
    "workspace",
    "projeto",
    "arquivo",
    "arquivos",
    "estrutura",
    "arquitetura",
    "repo",
    "repositório",
    "diretório",
    "diretorio",
    "pasta",
    "acessar",
    "abrir",
    "listar",
    "verificar",
    "mostrar",
    "ler",
    "conteúdo",
    "conteudo",
)


@dataclass(slots=True, frozen=True)
class IntentDecision:
    use_agent: bool
    role: ModelRole
    reason: str


class IntentClassifier:
    def classify(self, prompt: str, file: str | None = None) -> IntentDecision:
        text = (prompt or "").lower().strip()

        if file:
            suffix = Path(file).suffix.lower()
            if suffix in VISION_SUFFIXES:
                return IntentDecision(
                    use_agent=False,
                    role=ModelRole.VISION,
                    reason="arquivo visual",
                )

        if self._looks_like_workspace_path(text):
            return IntentDecision(
                use_agent=True,
                role=ModelRole.DEFAULT,
                reason="prompt com caminho de workspace",
            )

        if any(hint in text for hint in ENGINEERING_HINTS):
            return IntentDecision(
                use_agent=True,
                role=ModelRole.DEFAULT,
                reason="pedido de engenharia",
            )

        if any(hint in text for hint in WORKSPACE_HINTS):
            return IntentDecision(
                use_agent=True,
                role=ModelRole.DEFAULT,
                reason="pedido ligado ao workspace",
            )

        return IntentDecision(
            use_agent=False,
            role=ModelRole.DEFAULT,
            reason="conversa direta",
        )

    def _looks_like_workspace_path(self, text: str) -> bool:
        if re.search(r"[a-zA-Z]:\\", text):
            return True
        if re.search(r"[a-zA-Z0-9_\-]+[\\/][a-zA-Z0-9_\-]+", text):
            return True
        return False
