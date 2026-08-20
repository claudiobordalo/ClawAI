from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from .response import ProviderResponse


class BaseProvider(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:
        pass
