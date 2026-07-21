from __future__ import annotations

from typing import Any

from clawai.tools.tool import Tool
from clawai.tools.tool_descriptor import ToolDescriptor
from clawai.tools.tool_registry import ToolRegistry


class ToolDiscovery:
    """
    Responsabilidade única:
    - Expor descrições padronizadas das ferramentas registradas no ToolRegistry.

    Fluxo:
    1. Receber uma instância de ToolRegistry.
    2. Obter todas as ferramentas registradas.
    3. Converter cada ferramenta para um ToolDescriptor via describe().
    4. Retornar uma lista ordenada deterministicamente por nome.

    Regras:
    - Não executa ferramentas.
    - Não acessa ToolExecutor.
    - Não acessa AgentEngine.
    - Não acessa AgentLoop.
    - Não acessa Providers.
    - Não monta prompts.
    - Não interpreta respostas do LLM.
    """

    def __init__(self, *, tool_registry: ToolRegistry) -> None:
        if tool_registry is None:
            raise ValueError("ToolDiscovery: 'tool_registry' é obrigatório.")

        self._tool_registry = tool_registry

    @property
    def tool_registry(self) -> ToolRegistry:
        return self._tool_registry

    def discover_all(self) -> tuple[ToolDescriptor, ...]:
        """
        Retorna todos os ToolDescriptors das ferramentas registradas,
        ordenados deterministicamente por nome.

        Returns:
            Tupla de ToolDescriptor ordenada por nome.
        """
        list_result = self._tool_registry.list_tools()
        if not list_result.get("success", False):
            return ()

        tool_names: list[str] = list_result.get("result", [])
        if not tool_names:
            return ()

        descriptors: list[ToolDescriptor] = []
        for name in sorted(tool_names):
            get_result = self._tool_registry.get(name)
            if not get_result.get("success", False):
                continue

            tool: Any = get_result.get("result")
            if tool is None:
                continue

            descriptor = self._describe_tool(tool)
            if descriptor is not None:
                descriptors.append(descriptor)

        return tuple(sorted(descriptors, key=lambda d: d.name))

    def discover(self, name: str) -> ToolDescriptor | None:
        """
        Retorna o ToolDescriptor de uma ferramenta específica pelo nome.

        Args:
            name: Nome da ferramenta.

        Returns:
            ToolDescriptor se a ferramenta existir, None caso contrário.
        """
        get_result = self._tool_registry.get(name)
        if not get_result.get("success", False):
            return None

        tool: Any = get_result.get("result")
        if tool is None:
            return None

        return self._describe_tool(tool)

    def _describe_tool(self, tool: Any) -> ToolDescriptor | None:
        """
        Tenta obter o ToolDescriptor de uma ferramenta, com fallback
        para metadados básicos quando describe() não está disponível.

        Args:
            tool: Instância da ferramenta.

        Returns:
            ToolDescriptor ou None se a ferramenta for inválida.
        """
        if tool is None:
            return None

        # Se a ferramenta implementa describe(), usa-o
        describe_fn = getattr(tool, "describe", None)
        if callable(describe_fn):
            try:
                result = describe_fn()
                if isinstance(result, ToolDescriptor):
                    return result
            except Exception:
                pass

        # Fallback: constrói descrição mínima a partir de name/description
        name = self._safe_get_str(tool, "name")
        description = self._safe_get_str(tool, "description")

        if not name:
            return None

        return ToolDescriptor(
            name=name,
            description=description or "",
        )

    @staticmethod
    def _safe_get_str(obj: Any, attr: str) -> str:
        """Obtém um atributo string de forma segura."""
        try:
            value = getattr(obj, attr, None)
            if value is not None:
                return str(value)
        except Exception:
            pass
        return ""