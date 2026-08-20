from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clawai.providers.base.provider import BaseProvider
from clawai.providers.base.response import ProviderResponse
from clawai.prompt.prompt_engine import PromptEngine


@dataclass(slots=True, frozen=True)
class LLMResult:
    """
    Resultado padronizado da execução do LLM.

    Attributes:
        success: Indica se a execução foi bem-sucedida.
        response: ProviderResponse original quando sucesso, ou None.
        error: Mensagem de erro quando falha, ou None.
    """

    success: bool
    response: ProviderResponse | None = None
    error: str | None = None


class LLMExecutor:
    """
    Responsabilidade única:
    - Orquestrar a chamada ao modelo de linguagem utilizando o PromptEngine e um Provider,
      sem conhecer implementações concretas.

    Fluxo:
    1. Receber Mission, ContextBuilderResult, Workspace, User Instruction.
    2. Solicitar ao PromptEngine a construção do prompt.
    3. Enviar o prompt para um Provider injetado via DI.
    4. Retornar exatamente o resultado produzido pelo Provider.
    5. Capturar exceções e retornar erro padronizado.

    Regras:
    - Não monta prompts manualmente.
    - Não conhece implementações concretas de Providers.
    - Não acessa ToolRegistry.
    - Não executa Tools.
    - Não modifica Workspace.
    - Não conhece Dispatcher.
    - Não conhece ActionExecutor.
    - Não contém lógica de negócio.
    """

    def __init__(
        self,
        *,
        prompt_engine: PromptEngine,
        provider: BaseProvider,
    ) -> None:
        if prompt_engine is None:
            raise ValueError("LLMExecutor: 'prompt_engine' é obrigatório.")
        if provider is None:
            raise ValueError("LLMExecutor: 'provider' é obrigatório.")

        self._prompt_engine = prompt_engine
        self._provider = provider

    @property
    def prompt_engine(self) -> PromptEngine:
        return self._prompt_engine

    @property
    def provider(self) -> BaseProvider:
        return self._provider

    def execute(
        self,
        *,
        mission: Any,
        context_builder_result: Any,
        workspace: Any,
        user_instruction: str,
    ) -> LLMResult:
        """
        Executa o fluxo completo: PromptEngine -> Provider.

        Args:
            mission: Missão atual.
            context_builder_result: Resultado do ContextBuilder.
            workspace: Workspace atual.
            user_instruction: Instrução do usuário.

        Returns:
            LLMResult com o resultado do Provider ou erro padronizado.
        """
        if mission is None:
            return LLMResult(success=False, error="LLMExecutor: 'mission' é obrigatório.")
        if context_builder_result is None:
            return LLMResult(success=False, error="LLMExecutor: 'context_builder_result' é obrigatório.")
        if workspace is None:
            return LLMResult(success=False, error="LLMExecutor: 'workspace' é obrigatório.")
        if not user_instruction:
            return LLMResult(success=False, error="LLMExecutor: 'user_instruction' é obrigatório.")

        try:
            prompt = self._prompt_engine.build(
                mission=mission,
                context_builder_result=context_builder_result,
                workspace=workspace,
                user_instruction=user_instruction,
            )
        except Exception as exc:
            return LLMResult(
                success=False,
                error=f"LLMExecutor: falha no PromptEngine: {exc}",
            )

        try:
            response = self._provider.generate(prompt=prompt)
        except Exception as exc:
            return LLMResult(
                success=False,
                error=f"LLMExecutor: falha no Provider: {exc}",
            )

        return LLMResult(success=True, response=response)