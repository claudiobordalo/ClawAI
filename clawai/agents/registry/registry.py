from __future__ import annotations

from typing import Type, Dict, Any

from clawai.agents.agent import Agent


class AgentRegistry:
    """Central registry for agent types."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[Agent]] = {}

    def register(self, name: str, agent_class: Type[Agent]) -> None:
        self._registry[name] = agent_class

    def get(self, name: str) -> Type[Agent]:
        if name not in self._registry:
            raise KeyError(f"Agent '{name}' not found in registry.")
        return self._registry[name]

    def list_agents(self) -> list[str]:
        return list(self._registry.keys())


# Singleton instance
registry = AgentRegistry()
