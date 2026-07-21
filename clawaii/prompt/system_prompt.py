from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SystemPrompt:
    """
    Componente responsável por armazenar e fornecer as instruções
    permanentes (System Prompt) do agente.

    Imutável após criação; build() retorna o texto tal como armazenado.
    """

    content: str = ""

    def build(self) -> str:
        return self.content
