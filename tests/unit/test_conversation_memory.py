from __future__ import annotations

import pytest

from clawai.memory.conversation_memory import ConversationHistory
from clawai.memory.conversation_memory import ConversationMemory
from clawai.memory.conversation_memory import ConversationMessage


# ---------------------------------------------------------------------------
# Adicionar mensagens
# ---------------------------------------------------------------------------


def test_add_message() -> None:
    """Adicionar uma mensagem ao histórico."""
    memory = ConversationMemory()
    msg = memory.add(role="user", content="Hello")

    assert isinstance(msg, ConversationMessage)
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.metadata == {}
    assert msg.timestamp != ""  # timestamp automático


def test_add_message_with_metadata() -> None:
    """Adicionar mensagem com metadados."""
    memory = ConversationMemory()
    msg = memory.add(
        role="assistant",
        content="Resposta",
        metadata={"model": "gpt-4", "tokens": 150},
    )

    assert msg.role == "assistant"
    assert msg.content == "Resposta"
    assert msg.metadata == {"model": "gpt-4", "tokens": 150}


def test_add_message_returns_message_with_timestamp() -> None:
    """Mensagem adicionada recebe timestamp automático ISO 8601."""
    memory = ConversationMemory()
    msg = memory.add(role="user", content="test")

    assert "T" in msg.timestamp  # ISO 8601 contém 'T'
    assert msg.timestamp.endswith("Z") or "+" in msg.timestamp


# ---------------------------------------------------------------------------
# Recuperar todas as mensagens
# ---------------------------------------------------------------------------


def test_messages_returns_all_added() -> None:
    """messages() retorna todas as mensagens adicionadas."""
    memory = ConversationMemory()
    memory.add(role="user", content="msg1")
    memory.add(role="assistant", content="msg2")
    memory.add(role="user", content="msg3")

    all_msgs = memory.messages()
    assert len(all_msgs) == 3
    assert all_msgs[0].content == "msg1"
    assert all_msgs[1].content == "msg2"
    assert all_msgs[2].content == "msg3"


def test_messages_returns_tuple() -> None:
    """messages() retorna uma tupla (imutável)."""
    memory = ConversationMemory()
    memory.add(role="user", content="test")

    msgs = memory.messages()
    assert isinstance(msgs, tuple)


# ---------------------------------------------------------------------------
# Recuperar últimas N
# ---------------------------------------------------------------------------


def test_last_n_returns_correct_count() -> None:
    """last(n) retorna exatamente as últimas N mensagens."""
    memory = ConversationMemory()
    for i in range(5):
        memory.add(role="user", content=f"msg{i}")

    last_3 = memory.last(3)
    assert len(last_3) == 3
    assert last_3[0].content == "msg2"
    assert last_3[1].content == "msg3"
    assert last_3[2].content == "msg4"


def test_last_n_greater_than_size() -> None:
    """last(n) com n maior que o total retorna todas."""
    memory = ConversationMemory()
    memory.add(role="user", content="única")

    last_10 = memory.last(10)
    assert len(last_10) == 1


def test_last_zero_returns_empty() -> None:
    """last(0) retorna tupla vazia."""
    memory = ConversationMemory()
    memory.add(role="user", content="test")

    result = memory.last(0)
    assert result == ()


def test_last_negative_raises() -> None:
    """last(n) com n negativo dispara ValueError."""
    memory = ConversationMemory()
    with pytest.raises(ValueError, match="n"):
        memory.last(-1)


# ---------------------------------------------------------------------------
# Limpar histórico
# ---------------------------------------------------------------------------


def test_clear_removes_all_messages() -> None:
    """clear() remove todas as mensagens."""
    memory = ConversationMemory()
    memory.add(role="user", content="msg1")
    memory.add(role="user", content="msg2")
    assert memory.size() == 2

    memory.clear()
    assert memory.size() == 0
    assert memory.messages() == ()


def test_clear_empty_memory() -> None:
    """clear() em memória vazia não causa erro."""
    memory = ConversationMemory()
    memory.clear()
    assert memory.size() == 0


# ---------------------------------------------------------------------------
# Histórico vazio
# ---------------------------------------------------------------------------


def test_empty_memory_size_zero() -> None:
    """Memória recém-criada tem size() == 0."""
    memory = ConversationMemory()
    assert memory.size() == 0


def test_empty_memory_messages_empty() -> None:
    """messages() em memória vazia retorna tupla vazia."""
    memory = ConversationMemory()
    assert memory.messages() == ()


def test_empty_memory_last_zero() -> None:
    """last(0) em memória vazia retorna tupla vazia."""
    memory = ConversationMemory()
    assert memory.last(0) == ()


def test_empty_memory_last_positive() -> None:
    """last(n) em memória vazia retorna tupla vazia."""
    memory = ConversationMemory()
    assert memory.last(5) == ()


# ---------------------------------------------------------------------------
# Preservação da ordem
# ---------------------------------------------------------------------------


def test_messages_preserve_insertion_order() -> None:
    """Mensagens são retornadas na ordem de inserção."""
    memory = ConversationMemory()
    memory.add(role="user", content="primeira")
    memory.add(role="assistant", content="segunda")
    memory.add(role="user", content="terceira")
    memory.add(role="system", content="quarta")

    msgs = memory.messages()
    assert [m.content for m in msgs] == [
        "primeira",
        "segunda",
        "terceira",
        "quarta",
    ]


def test_last_preserves_order() -> None:
    """last(n) mantém ordem cronológica."""
    memory = ConversationMemory()
    for i in range(5):
        memory.add(role="user", content=f"msg{i}")

    last_2 = memory.last(2)
    assert last_2[0].content == "msg3"
    assert last_2[1].content == "msg4"


# ---------------------------------------------------------------------------
# Timestamp automático
# ---------------------------------------------------------------------------


def test_auto_timestamp_on_add() -> None:
    """add() gera timestamp automaticamente."""
    memory = ConversationMemory()
    msg = memory.add(role="user", content="teste")

    assert isinstance(msg.timestamp, str)
    assert len(msg.timestamp) > 0
    assert "T" in msg.timestamp  # formato ISO 8601


def test_explicit_timestamp_is_preserved() -> None:
    """Timestamp explícito não é sobrescrito."""
    memory = ConversationMemory()
    msg = memory.add(role="user", content="teste")

    # Cria mensagem com timestamp explícito
    explicit = ConversationMessage(
        role="system",
        content="init",
        timestamp="2024-01-01T00:00:00Z",
    )

    assert explicit.timestamp == "2024-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Metadata opcional
# ---------------------------------------------------------------------------


def test_default_metadata_is_empty_dict() -> None:
    """Sem metadata, o padrão é dicionário vazio."""
    memory = ConversationMemory()
    msg = memory.add(role="user", content="test")

    assert msg.metadata == {}


def test_metadata_preserved() -> None:
    """Metadados fornecidos são preservados."""
    memory = ConversationMemory()
    meta = {"key": "value", "count": 42}
    msg = memory.add(role="user", content="test", metadata=meta)

    assert msg.metadata == meta


# ---------------------------------------------------------------------------
# size()
# ---------------------------------------------------------------------------


def test_size_after_add() -> None:
    """size() reflete o número de mensagens adicionadas."""
    memory = ConversationMemory()
    assert memory.size() == 0

    memory.add(role="user", content="a")
    assert memory.size() == 1

    memory.add(role="user", content="b")
    assert memory.size() == 2

    memory.add(role="user", content="c")
    assert memory.size() == 3


def test_size_after_clear() -> None:
    """size() após clear() retorna 0."""
    memory = ConversationMemory()
    memory.add(role="user", content="a")
    memory.add(role="user", content="b")
    assert memory.size() == 2

    memory.clear()
    assert memory.size() == 0


# ---------------------------------------------------------------------------
# Imutabilidade das dataclasses
# ---------------------------------------------------------------------------


def test_conversation_message_immutable() -> None:
    """ConversationMessage é frozen (imutável)."""
    msg = ConversationMessage(role="user", content="test")

    with pytest.raises(AttributeError):
        msg.role = "assistant"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        msg.content = "novo"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        msg.timestamp = "2024-01-01"  # type: ignore[misc]


def test_conversation_history_immutable() -> None:
    """ConversationHistory é frozen (imutável)."""
    history = ConversationHistory()

    with pytest.raises(AttributeError):
        history.messages = ()  # type: ignore[misc]


def test_conversation_message_has_slots() -> None:
    """ConversationMessage usa slots para eficiência."""
    msg = ConversationMessage(role="user", content="test")

    # Confirmar que os campos existem
    assert msg.role == "user"
    assert msg.content == "test"

    # Slots impedem criação de novos atributos (frozen + slots)
    with pytest.raises((AttributeError, TypeError)):
        msg.novo_atributo = "valor"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Validação de entradas
# ---------------------------------------------------------------------------


def test_add_empty_role_raises() -> None:
    """add() com role vazio dispara ValueError."""
    memory = ConversationMemory()
    with pytest.raises(ValueError, match="role"):
        memory.add(role="", content="test")


def test_add_none_content_raises() -> None:
    """add() com content=None dispara ValueError."""
    memory = ConversationMemory()
    with pytest.raises(ValueError, match="content"):
        memory.add(role="user", content=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Estabilidade entre chamadas
# ---------------------------------------------------------------------------


def test_multiple_calls_consistent() -> None:
    """Múltiplas chamadas a messages() retornam o mesmo estado."""
    memory = ConversationMemory()
    memory.add(role="user", content="msg1")
    memory.add(role="assistant", content="msg2")

    first_call = memory.messages()
    second_call = memory.messages()

    assert first_call == second_call


def test_add_does_not_affect_previous_messages() -> None:
    """
    Adicionar novas mensagens não altera as mensagens
    previamente retornadas.
    """
    memory = ConversationMemory()
    memory.add(role="user", content="msg1")

    first_snapshot = memory.messages()

    memory.add(role="assistant", content="msg2")

    # A primeira mensagem permanece inalterada
    assert first_snapshot[0].content == "msg1"
    assert len(first_snapshot) == 1

    # O estado atual contém ambas
    assert memory.size() == 2


# ---------------------------------------------------------------------------
# ConversationHistory
# ---------------------------------------------------------------------------


def test_conversation_history_default_empty() -> None:
    """ConversationHistory padrão tem tupla vazia."""
    history = ConversationHistory()
    assert history.messages == ()


def test_conversation_history_with_messages() -> None:
    """ConversationHistory com mensagens."""
    msg1 = ConversationMessage(role="user", content="Hello")
    msg2 = ConversationMessage(role="assistant", content="Hi")

    history = ConversationHistory(messages=(msg1, msg2))
    assert len(history.messages) == 2
    assert history.messages[0].content == "Hello"
    assert history.messages[1].content == "Hi"


# ---------------------------------------------------------------------------
# ConversationMessage post_init
# ---------------------------------------------------------------------------


def test_conversation_message_post_init_sets_timestamp() -> None:
    """__post_init__ define timestamp quando não fornecido."""
    msg = ConversationMessage(role="user", content="test")
    assert msg.timestamp != ""


def test_conversation_message_post_init_preserves_explicit_timestamp() -> None:
    """__post_init__ preserva timestamp explícito."""
    msg = ConversationMessage(
        role="user",
        content="test",
        timestamp="2023-06-01T10:00:00Z",
    )
    assert msg.timestamp == "2023-06-01T10:00:00Z"