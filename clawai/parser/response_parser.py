from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from clawai.providers.base.response import ProviderResponse

# Action contract compatible with ActionExecutor
Action = dict[str, Any]


@dataclass(slots=True, frozen=True)
class ParseResult:
    """
    Resultado padronizado da interpretação da resposta do LLM.

    Attributes:
        success: Indica se o parsing foi bem-sucedido.
        action: Action estruturada quando sucesso, ou None.
        error: Mensagem de erro quando falha, ou None.
    """

    success: bool
    action: Action | None = None
    error: str | None = None


class ResponseParser:
    """
    Responsabilidade única:
    - Interpretar a resposta textual do ProviderResponse e produzir
      uma estrutura padronizada de Action compatível com o ActionExecutor.

    Fluxo:
    1. Extrair conteúdo textual do ProviderResponse.
    2. Tentar fazer parse como JSON.
    3. Validar campos obrigatórios conforme o tipo de Action.
    4. Retornar ParseResult com a Action estruturada ou erro padronizado.

    Regras:
    - Não executa Actions.
    - Não acessa ToolRegistry.
    - Não acessa ToolExecutor.
    - Não acessa ActionExecutor.
    - Não acessa Dispatcher.
    - Não acessa Workspace.
    - Não modifica Mission.
    - Apenas interpreta a resposta.
    """

    # Tipos de Action suportados e seus campos obrigatórios.
    # Facilmente extensível para novos tipos de Action.
    _ACTION_SCHEMAS: dict[str, set[str]] = {
        "tool": {"tool", "arguments"},
    }

    def parse(self, response: ProviderResponse) -> ParseResult:
        """
        Interpreta um ProviderResponse e retorna um ParseResult padronizado.

        Args:
            response: Resposta do Provider contendo o conteúdo textual do LLM.

        Returns:
            ParseResult com Action estruturada ou erro padronizado.
        """
        if response is None:
            return ParseResult(
                success=False,
                error="ResponseParser: 'response' é obrigatório.",
            )

        content = response.content

        if not content or not content.strip():
            return ParseResult(
                success=False,
                error="ResponseParser: resposta vazia.",
            )

        # Tentar extrair bloco JSON da resposta (o LLM pode incluir markdown)
        raw = content.strip()

        # Suporta respostas com bloco de código ```json ... ```
        json_str = self._extract_json(raw)

        try:
            data: dict[str, Any] = json.loads(json_str)
        except json.JSONDecodeError:
            return ParseResult(
                success=False,
                error="ResponseParser: JSON inválido na resposta do LLM.",
            )

        if not isinstance(data, dict):
            return ParseResult(
                success=False,
                error="ResponseParser: JSON deve ser um objeto.",
            )

        # Validar tipo de Action
        action_type = data.get("type")
        if not action_type:
            return ParseResult(
                success=False,
                action=None,
                error="ResponseParser: campo 'type' obrigatório ausente.",
            )

        if not isinstance(action_type, str):
            return ParseResult(
                success=False,
                error="ResponseParser: campo 'type' deve ser uma string.",
            )

        if action_type not in self._ACTION_SCHEMAS:
            return ParseResult(
                success=False,
                error=f"ResponseParser: tipo de Action desconhecido '{action_type}'.",
            )

        # Validar campos obrigatórios para o tipo
        required_fields = self._ACTION_SCHEMAS[action_type]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return ParseResult(
                success=False,
                error=(
                    f"ResponseParser: campos obrigatórios ausentes "
                    f"para Action tipo '{action_type}': {missing}."
                ),
            )

        # Validações específicas por tipo
        if action_type == "tool":
            tool_name = data.get("tool")
            if not isinstance(tool_name, str) or not tool_name.strip():
                return ParseResult(
                    success=False,
                    error="ResponseParser: campo 'tool' deve ser uma string não vazia.",
                )

            arguments = data.get("arguments")
            if not isinstance(arguments, dict):
                return ParseResult(
                    success=False,
                    error="ResponseParser: campo 'arguments' deve ser um dicionário.",
                )

        action: Action = {
            "type": action_type,
        }
        action.update(
            {k: v for k, v in data.items() if k != "type"}
        )

        return ParseResult(success=True, action=action, error=None)

    def _extract_json(self, raw: str) -> str:
        """
        Extrai um bloco JSON da resposta textual, suportando:
        - Código markdown ```json ... ```
        - ``` ... ```
        - Apenas o JSON puro
        """
        # Tentar extrair ```json ... ```
        json_markers = [
            ("```json", "```"),
            ("```", "```"),
        ]

        for start_marker, end_marker in json_markers:
            start_idx = raw.find(start_marker)
            if start_idx != -1:
                start_content = start_idx + len(start_marker)
                end_idx = raw.find(end_marker, start_content)
                if end_idx != -1:
                    return raw[start_content:end_idx].strip()

        # Se não encontrou marcador, retorna o conteúdo limpo
        return raw