from __future__ import annotations

from typing import Any


class ServiceContainer:
    """
    Simple Dependency Injection container.
    """

    def __init__(self) -> None:
        self._services: dict[type[Any], Any] = {}

    def register(
        self,
        interface: type[Any],
        implementation: Any,
    ) -> None:
        self._services[interface] = implementation

    def resolve(
        self,
        interface: type[Any],
    ) -> Any:

        if interface not in self._services:
            raise KeyError(
                f"Service '{interface.__name__}' is not registered."
            )

        return self._services[interface]

    def contains(
        self,
        interface: type[Any],
    ) -> bool:
        return interface in self._services

    def clear(self) -> None:
        self._services.clear()
