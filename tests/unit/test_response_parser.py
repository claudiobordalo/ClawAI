from __future__ import annotations

import pytest

from clawai.parser.response_parser import ParseResult
from clawai.parser.response_parser import ResponseParser
from clawai.providers.base.response import ProviderResponse


def _make_response(content: str) -> ProviderResponse:
    return ProviderResponse(
        content=content,
        model="gpt-4",
        provider="openai",
    )


# ---------------------------------------------------------------------------
# Parsing válido
# ---------------------------------------------------------------------------


def test_parse_valid_tool_action_json_puro() -> None:
    """
    Parsing válido de Action do tipo tool a partir de JSON puro.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.read_file", "arguments": {"path": "README.md"}}'
    )

    result = parser.parse(response)

    assert result.success is True
    assert result.error is None
    assert result.action is not None
    assert result.action["type"] == "tool"
    assert result.action["tool"] == "filesystem.read_file"
    assert result.action["arguments"] == {"path": "README.md"}


def test_parse_valid_tool_action_with_json_markdown_block() -> None:
    """
    Parsing válido quando o LLM retorna resposta com bloco ```json ... ```.
    """
    parser = ResponseParser()
    content = """
Aqui está a ação solicitada:

```json
{
    "type": "tool",
    "tool": "filesystem.write_file",
    "arguments": {
        "path": "test.txt",
        "content": "Hello"
    }
}
```

Executando agora...
"""
    response = _make_response(content)

    result = parser.parse(response)

    assert result.success is True
    assert result.action is not None
    assert result.action["type"] == "tool"
    assert result.action["tool"] == "filesystem.write_file"
    assert result.action["arguments"] == {"path": "test.txt", "content": "Hello"}


def test_parse_valid_tool_action_with_generic_code_block() -> None:
    """
    Parsing válido com bloco ``` (sem linguagem especificada).
    """
    parser = ResponseParser()
    content = """
```
{"type": "tool", "tool": "filesystem.search", "arguments": {"pattern": "*.py"}}
```
"""
    response = _make_response(content)

    result = parser.parse(response)

    assert result.success is True
    assert result.action is not None
    assert result.action["type"] == "tool"
    assert result.action["tool"] == "filesystem.search"
    assert result.action["arguments"] == {"pattern": "*.py"}


def test_parse_valid_tool_action_with_extra_fields() -> None:
    """
    Parsing válido quando a resposta contém campos extras além dos obrigatórios.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.read_file", "arguments": {"path": "a.txt"}, "extra": "campo adicional"}'
    )

    result = parser.parse(response)

    assert result.success is True
    assert result.action is not None
    assert result.action["type"] == "tool"
    assert result.action["tool"] == "filesystem.read_file"
    assert result.action["arguments"] == {"path": "a.txt"}
    assert result.action["extra"] == "campo adicional"


def test_parse_valid_tool_action_empty_arguments() -> None:
    """
    Parsing válido com argumentos vazios (dicionário vazio é válido).
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.list_dir", "arguments": {}}'
    )

    result = parser.parse(response)

    assert result.success is True
    assert result.action is not None
    assert result.action["type"] == "tool"
    assert result.action["tool"] == "filesystem.list_dir"
    assert result.action["arguments"] == {}


# ---------------------------------------------------------------------------
# Estabilidade determinística
# ---------------------------------------------------------------------------


def test_parse_stability_same_input_produces_same_output() -> None:
    """
    O parser é determinístico: mesma entrada sempre produz mesma saída.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.read_file", "arguments": {"path": "x.txt"}}'
    )

    result1 = parser.parse(response)
    result2 = parser.parse(response)

    assert result1.success == result2.success
    assert result1.action == result2.action
    assert result1.error == result2.error


# ---------------------------------------------------------------------------
# Tratamento de erros: resposta vazia / ausente
# ---------------------------------------------------------------------------


def test_parse_response_none_returns_error() -> None:
    """
    ProviderResponse None retorna erro padronizado.
    """
    parser = ResponseParser()

    result = parser.parse(None)  # type: ignore[arg-type]

    assert result.success is False
    assert result.action is None
    assert result.error is not None
    assert "response" in result.error
    assert "obrigatório" in result.error


def test_parse_empty_content_returns_error() -> None:
    """
    Resposta vazia retorna erro padronizado.
    """
    parser = ResponseParser()
    response = _make_response("")

    result = parser.parse(response)

    assert result.success is False
    assert result.action is None
    assert result.error is not None
    assert "vazia" in result.error


def test_parse_whitespace_only_content_returns_error() -> None:
    """
    Resposta com apenas espaços em branco retorna erro.
    """
    parser = ResponseParser()
    response = _make_response("   \n  \t  ")

    result = parser.parse(response)

    assert result.success is False
    assert result.error is not None
    assert "vazia" in result.error


# ---------------------------------------------------------------------------
# Tratamento de erros: JSON inválido
# ---------------------------------------------------------------------------


def test_parse_invalid_json_returns_error() -> None:
    """
    JSON inválido retorna erro padronizado.
    """
    parser = ResponseParser()
    response = _make_response("isso não é um json válido")

    result = parser.parse(response)

    assert result.success is False
    assert result.action is None
    assert result.error is not None
    assert "JSON inválido" in result.error


def test_parse_malformed_json_in_code_block_returns_error() -> None:
    """
    JSON mal formatado dentro de bloco de código retorna erro.
    """
    parser = ResponseParser()
    response = _make_response(
        "```json\n{ tipo errado aqui }\n```"
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.error is not None
    assert "JSON inválido" in result.error


def test_parse_json_array_returns_error() -> None:
    """
    JSON que não é um objeto (ex: array) retorna erro.
    """
    parser = ResponseParser()
    response = _make_response('["item1", "item2"]')

    result = parser.parse(response)

    assert result.success is False
    assert result.error is not None
    assert "JSON deve ser um objeto" in result.error


# ---------------------------------------------------------------------------
# Tratamento de erros: campos obrigatórios
# ---------------------------------------------------------------------------


def test_parse_missing_type_field_returns_error() -> None:
    """
    Ausência do campo 'type' retorna erro padronizado.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"tool": "filesystem.read_file", "arguments": {"path": "a.txt"}}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.action is None
    assert result.error is not None
    assert "type" in result.error
    assert "obrigatório" in result.error


def test_parse_missing_tool_field_returns_error() -> None:
    """
    Ausência do campo 'tool' para Action tipo 'tool' retorna erro.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "arguments": {"path": "a.txt"}}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.action is None
    assert result.error is not None
    assert "tool" in result.error
    assert "obrigatórios" in result.error


def test_parse_missing_arguments_field_returns_error() -> None:
    """
    Ausência do campo 'arguments' para Action tipo 'tool' retorna erro.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.read_file"}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.action is None
    assert result.error is not None
    assert "arguments" in result.error
    assert "obrigatórios" in result.error


def test_parse_type_not_string_returns_error() -> None:
    """
    Campo 'type' que não é string retorna erro.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": 123, "tool": "filesystem.read_file", "arguments": {}}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.error is not None
    assert "type" in result.error
    assert "string" in result.error


# ---------------------------------------------------------------------------
# Tratamento de erros: tipo de Action desconhecido
# ---------------------------------------------------------------------------


def test_parse_unknown_action_type_returns_error() -> None:
    """
    Tipo de Action desconhecido retorna erro padronizado.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "invalid_type", "some_field": "value"}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.action is None
    assert result.error is not None
    assert "desconhecido" in result.error
    assert "invalid_type" in result.error


# ---------------------------------------------------------------------------
# Tratamento de erros: validação específica de tipos
# ---------------------------------------------------------------------------


def test_parse_tool_not_string_returns_error() -> None:
    """
    Campo 'tool' que não é string retorna erro.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": 42, "arguments": {}}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.error is not None
    assert "tool" in result.error
    assert "string" in result.error


def test_parse_tool_empty_string_returns_error() -> None:
    """
    Campo 'tool' vazio retorna erro.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "", "arguments": {}}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.error is not None
    assert "tool" in result.error
    assert "string não vazia" in result.error


def test_parse_arguments_not_dict_returns_error() -> None:
    """
    Campo 'arguments' que não é dict retorna erro.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.read_file", "arguments": "string_invalida"}'
    )

    result = parser.parse(response)

    assert result.success is False
    assert result.error is not None
    assert "arguments" in result.error
    assert "dicionário" in result.error


# ---------------------------------------------------------------------------
# Propagação correta dos resultados
# ---------------------------------------------------------------------------


def test_parse_adheres_to_parse_result_contract() -> None:
    """
    ParseResult sempre contém success, action, error no contrato padronizado.
    """
    parser = ResponseParser()

    # Caso sucesso
    response_ok = _make_response(
        '{"type": "tool", "tool": "filesystem.read_file", "arguments": {"path": "x"}}'
    )
    result_ok = parser.parse(response_ok)
    assert hasattr(result_ok, "success")
    assert hasattr(result_ok, "action")
    assert hasattr(result_ok, "error")
    assert result_ok.success is True
    assert result_ok.action is not None
    assert result_ok.error is None

    # Caso erro
    response_fail = _make_response("")
    result_fail = parser.parse(response_fail)
    assert result_fail.success is False
    assert result_fail.action is None
    assert result_fail.error is not None


def test_parse_result_dataclass_immutability() -> None:
    """
    ParseResult é imutável (dataclass frozen).
    """
    result = ParseResult(success=True, action={"type": "tool"}, error=None)

    with pytest.raises(AttributeError):
        result.success = False  # type: ignore[misc]

    with pytest.raises(AttributeError):
        result.action = None  # type: ignore[misc]


def test_parse_propagates_action_compatible_with_action_executor() -> None:
    """
    A Action produzida pelo ResponseParser é compatível com o contrato
    esperado pelo ActionExecutor.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.read_file", "arguments": {"path": "main.py"}}'
    )

    result = parser.parse(response)

    assert result.success is True
    assert result.action is not None

    # Contrato esperado pelo ActionExecutor
    action = result.action
    assert isinstance(action, dict)
    assert action["type"] == "tool"
    assert action["tool"] == "filesystem.read_file"
    assert isinstance(action["arguments"], dict)
    assert action["arguments"]["path"] == "main.py"


# ---------------------------------------------------------------------------
# Testes com markdown variado
# ---------------------------------------------------------------------------


def test_parse_with_text_before_and_after_markdown() -> None:
    """
    LLM pode incluir texto explicativo antes e depois do bloco JSON.
    """
    parser = ResponseParser()
    content = """Vou executar a leitura do arquivo:

```json
{"type": "tool", "tool": "filesystem.read_file", "arguments": {"path": "README.md"}}
```

Aguarde um momento...
"""
    response = _make_response(content)

    result = parser.parse(response)

    assert result.success is True
    assert result.action is not None
    assert result.action["tool"] == "filesystem.read_file"
    assert result.action["arguments"] == {"path": "README.md"}


def test_parse_with_only_json_no_markdown_extraction_needed() -> None:
    """
    JSON puro sem markdown é processado corretamente.
    """
    parser = ResponseParser()
    response = _make_response(
        '{"type": "tool", "tool": "filesystem.delete_file", "arguments": {"path": "tmp.txt"}}'
    )

    result = parser.parse(response)

    assert result.success is True
    assert result.action["tool"] == "filesystem.delete_file"


# ---------------------------------------------------------------------------
# Extensibilidade
# ---------------------------------------------------------------------------


def test_parser_is_extensible_for_new_action_types() -> None:
    """
    Verifica que a estrutura interna permite adicionar novos tipos de Action.
    """
    # ResponseParser começa apenas com "tool"
    parser = ResponseParser()

    # Apenas verifica que _ACTION_SCHEMAS existe e pode ser estendido
    schemas = parser._ACTION_SCHEMAS  # type: ignore[arg-type]  # acesso para teste
    assert "tool" in schemas
    assert schemas["tool"] == {"tool", "arguments"}