from __future__ import annotations

from typing import Any, Sequence, Tuple

from clawai.tools.tool_descriptor import ToolDescriptor


class ToolSelectionPolicy:
    """
    Política determinística para selecionar quais ferramentas serão expostas ao LLM.

    Esta implementação atual é simples e serve como ponto de extensão para
    políticas futuras mais inteligentes.
    """

    def select(
        self,
        tools: Sequence[ToolDescriptor],
        mission: Any,
        workspace: Any,
    ) -> Tuple[ToolDescriptor, ...]:
        """
        Seleciona e retorna apenas as ferramentas válidas, ordenadas por nome
        e sem duplicatas.

        Args:
            tools: Sequência de ToolDescriptor a serem avaliados.
            mission: Missão corrente. Atualmente não influencia a seleção.
            workspace: Workspace corrente. Atualmente não influencia a seleção.

        Returns:
            Tupla ordenada e sem duplicatas de ToolDescriptor válidos.
        """
        if not tools:
            return ()

        canonical_tools: dict[str, ToolDescriptor] = {}
        for tool in tools:
            if not isinstance(tool, ToolDescriptor):
                continue

            if not tool.name or not isinstance(tool.name, str):
                continue

            if tool.name in canonical_tools:
                continue

            canonical_tools[tool.name] = tool

        sorted_tools = tuple(sorted(canonical_tools.values(), key=lambda tool: tool.name))
        return sorted_tools
