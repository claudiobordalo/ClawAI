from abc import ABC, abstractmethod
from typing import Any

class ConfigLoader(ABC):
    """
    Abstract base class for loading configuration settings.

    This class should be subclassed to provide specific implementation for different configuration sources.
    """

    @abstractmethod
    def load(self) -> dict[str, Any]:
        """
        Load the configuration data from a source and return it as a dictionary.

        :return: A dictionary containing the loaded configuration settings.
        """