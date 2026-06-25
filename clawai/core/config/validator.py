from abc import ABC, abstractmethod
from typing import Any

class ConfigValidator(ABC):
    @abstractmethod
    def validate(self, config: dict[str, Any]) -> None:
        pass