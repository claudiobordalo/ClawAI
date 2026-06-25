from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def execute(
        self,
        **kwargs: Any,
    ) -> Any:
        ...
