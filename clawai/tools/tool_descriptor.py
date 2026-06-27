from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class ArgumentDescriptor:
    """
    Descrição de um argumento esperado por uma ferramenta.

    Attributes:
        name: Nome do argumento.
        type: Tipo esperado (ex: "string", "integer", "boolean").
        description: Descrição do argumento.
        required: Se o argumento é obrigatório.
        default: Valor padrão, se houver.
    """

    name: str
    type: str
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass(slots=True, frozen=True)
class ToolDescriptor:
    """
    Descrição padronizada de uma ferramenta registrada.

    Attributes:
        name: Nome único da ferramenta.
        description: Descrição textual da ferramenta.
        arguments: Lista de ArgumentDescriptor esperados pela ferramenta.
        examples: Exemplos opcionais de uso.
        version: Versão opcional da ferramenta.
    """

    name: str
    description: str
    arguments: tuple[ArgumentDescriptor, ...] = ()
    examples: tuple[str, ...] = ()
    version: str = ""