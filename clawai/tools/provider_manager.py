from __future__ import annotations

from typing import Any

from clawai.tools.providers import BaseToolProvider, LocalToolProvider


class ProviderManager:
    def __init__(self, providers: dict[str, BaseToolProvider] | None = None) -> None:
        self._providers = providers or {}
        self._cache: dict[str, list[str]] = {}

    def register(self, name: str, provider: BaseToolProvider) -> None:
        self._providers[name] = provider
        self._cache.pop(name, None)

    def resolve(self, tool_name: str) -> tuple[str, BaseToolProvider | None]:
        for name, provider in self._providers.items():
            if tool_name in provider.list_tools():
                return name, provider
        return "local", self._providers.get("local")

    def list_tools(self) -> list[str]:
        tools: list[str] = []
        for provider in self._providers.values():
            tools.extend(provider.list_tools())
        return sorted(set(tools))

    def get_provider(self, name: str) -> BaseToolProvider | None:
        return self._providers.get(name)

    def get_tool(self, tool_name: str) -> tuple[str, Any] | None:
        provider_name, provider = self.resolve(tool_name)
        if provider is None:
            return None
        return provider_name, provider.get_tool(tool_name)

    def execute(
        self,
        tool_name: str,
        *,
        arguments: dict[str, Any] | None = None,
        provider_name: str | None = None,
    ) -> dict[str, Any]:
        args = arguments or {}
        provider = self._providers.get(provider_name) if provider_name else None
        if provider is None:
            resolved_name, resolved_provider = self.resolve(tool_name)
            provider_name = resolved_name
            provider = resolved_provider
        if provider is None:
            return {
                "success": False,
                "tool": tool_name,
                "result": None,
                "error": f"Provider not found for tool: {tool_name}",
                "duration_ms": 0.0,
            }
        return provider.execute(tool_name, **args)

    def build_default(self) -> "ProviderManager":
        manager = ProviderManager()
        manager.register("local", LocalToolProvider())
        return manager
