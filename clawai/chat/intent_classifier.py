from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    "refatore",
    "corrija",
    "implemente",
    "analise",
    "explore",
    "pesquise",
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