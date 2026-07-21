from __future__ import annotations

from typing import Any, Type

from clawai.agents.agent import Agent
from clawai.agents.registry.registry import registry


class AgentFactory:
    """Factory for creating agent instances."""

    def __init__(self, registry_instance: AgentRegistry | None = None) -> None:
        self.registry = registry_instance or registry

    def create(self, name: str, **kwargs: Any) -> Agent:
        agent_class = self.registry.get(name)
        return agent_class(**kwargs)

    def register(self, name: str, agent_class: Type[Agent]) -> None:
        self.registry.register(name, agent_class)


# Singleton instance
factory = AgentFactory()
