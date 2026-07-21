from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """Configuração centralizada do agente ClawAI.

    Esta classe agrupa configurações de arquitetura em uma única fonte de verdade
    e é preparada para ser carregada a partir de arquivos ou variáveis de ambiente
    no futuro, sem alterar os componentes existentes.
    """

    max_iterations: int = 10
    memory_messages_limit: int = 10
    provider_timeout: float = 30.0
    provider_temperature: float = 0.7
    provider_max_tokens: int = 1024
    enable_tools: bool = True
    enable_memory: bool = True
    enable_workspace: bool = True
    enable_system_prompt: bool = True
    enable_tool_discovery: bool = True
