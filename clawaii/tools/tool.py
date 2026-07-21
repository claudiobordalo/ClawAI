from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from clawai.tools.tool_descriptor import ToolDescriptor

RuntimeResult = dict[str, Any]


class Tool(ABC):
    """
    Interface mínima para Tools.

    Regras:
    - O chamador nunca deve depender de exceções; implementações devem
      retornar sempre o contrato de runtime_result.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(self, **kwargs: Any) -> RuntimeResult:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> RuntimeResult:
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> ToolDescriptor:
        """
        Retorna um ToolDescriptor descrevendo esta ferramenta.

        Deve ser implementada por cada Tool concreta, expondo
        nome, descrição, argumentos esperados, exemplos e versão.
        """
        raise NotImplementedError
