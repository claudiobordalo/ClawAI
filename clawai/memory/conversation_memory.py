from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True, frozen=True)
class ConversationMessage:
    """
    Mensagem individual da conversa.

    Attributes:
        role: Papel do remetente (ex: "user", "assistant", "system").
        content: Conteúdo textual da mensagem.
        timestamp: Timestamp ISO 8601 da criação (automático se não informado).
        metadata: Dicionário opcional com dados extras.
    """

    role: str
    content: str
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Se timestamp não foi fornecido, define automaticamente
        if not self.timestamp:
            # Usa object.__setattr__ porque o dataclass é frozen
            object.__setattr__(
                self,
                "timestamp",
                datetime.now(timezone.utc).isoformat(),
            )


@dataclass(slots=True, frozen=True)
class ConversationHistory:
    """
    Coleção imutável de mensagens da conversa.

    Attributes:
        messages: Tupla de ConversationMessage em ordem cronológica.
    """

    messages: tuple[ConversationMessage, ...] = ()


class ConversationMemory:
    """
    Responsabilidade única:
    - Armazenar e recuperar mensagens da conversa em memória.

    Funcionalidades:
    - add(role, content, metadata=None): adiciona mensagem.
    - messages(): retorna todo o histórico.
    - clear(): limpa o histórico.
    - last(n): retorna as últimas N mensagens.
    - size(): retorna o número de mensagens.

    Regras:
    - Ordem cronológica garantida.
    - Estrutura totalmente determinística.
    - Não conhece AgentEngine, AgentLoop, Workspace, PromptEngine,
      Providers ou ToolRegistry.
    - Apenas armazenamento em memória (sem persistência em disco).

    Preparada para futura persistência em SQLite, PostgreSQL, Redis
    ou Vector Database sem alteração da API pública.
    """

    def __init__(self) -> None:
        self._messages: list[ConversationMessage] = []

    def add(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """
        Adiciona uma nova mensagem ao histórico.

        Args:
            role: Papel do remetente.
            content: Conteúdo da mensagem.
            metadata: Metadados opcionais.

        Returns:
            A ConversationMessage recém-criada.
        """
        if not role:
            raise ValueError("ConversationMemory: 'role' é obrigatório.")
        if content is None:
            raise ValueError("ConversationMemory: 'content' é obrigatório.")

        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._messages.append(message)
        return message

    def messages(self) -> tuple[ConversationMessage, ...]:
        """
        Retorna todo o histórico de mensagens.

        Returns:
            Tupla de ConversationMessage em ordem cronológica.
        """
        return tuple(self._messages)

    def clear(self) -> None:
        """Limpa todo o histórico de mensagens."""
        self._messages.clear()

    def last(self, n: int) -> tuple[ConversationMessage, ...]:
        """
        Retorna as últimas N mensagens.

        Args:
            n: Número de mensagens a retornar.

        Returns:
            Tupla com as últimas N mensagens em ordem cronológica.
        """
        if n < 0:
            raise ValueError(
                f"ConversationMemory: 'n' deve ser >= 0 (recebido {n})."
            )
        return tuple(self._messages[-n:]) if n > 0 else ()

    def size(self) -> int:
        """
        Retorna o número total de mensagens no histórico.

        Returns:
            Número de mensagens.
        """
        return len(self._messages)