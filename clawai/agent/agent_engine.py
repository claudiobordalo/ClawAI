from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clawai.context.context_builder import ContextBuilder
from clawai.execution.action_executor import ActionExecutor
from clawai.llm.llm_executor import LLMExecutor
from clawai.parser.response_parser import ResponseParser

# RuntimeContract do ActionExecutor
RuntimeContract = dict[str, Any]


@dataclass(slots=True, frozen=True)
class AgentResult:
    """
    Resultado padronizado da execução completa do agente.

    Attributes:
        success: Indica se todo o ciclo foi bem-sucedido.
        llm_response: Resposta textual bruta do LLM, ou None.
        action: Action estruturada interpretada, ou None.
        execution_result: Resultado da execução da Action, ou None.
        error: Mensagem de erro quando falha, ou None.
    """

    success: bool
    llm_response: str | None = None
    action: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None
    error: str | None = None


class AgentEngine:
    """
    Responsabilidade única:
    - Orquestrar todo o ciclo de execução do agente, coordenando o fluxo
      entre os componentes existentes.

    Fluxo:
    1. Receber Mission, Workspace, User Instruction.
    2. Solicitar ao ContextBuilder o contexto atualizado.
    3. Solicitar ao LLMExecutor a resposta do modelo.
    4. Enviar a resposta ao ResponseParser.
    5. Caso exista uma Action válida, encaminhá-la ao ActionExecutor.
    6. Retornar um resultado padronizado (AgentResult).

    Regras:
    - Não conhece ToolRegistry.
    - Não conhece ToolExecutor.
    - Não conhece Providers concretos.
    - Não monta prompts.
    - Não interpreta respostas.
    - Não executa ferramentas diretamente.
    - Apenas orquestra.
    """

    def __init__(
        self,
        *,
        context_builder: ContextBuilder,
        llm_executor: LLMExecutor,
        response_parser: ResponseParser,
        action_executor: ActionExecutor,
    ) -> None:
        if context_builder is None:
            raise ValueError("AgentEngine: 'context_builder' é obrigatório.")
        if llm_executor is None:
            raise ValueError("AgentEngine: 'llm_executor' é obrigatório.")
        if response_parser is None:
            raise ValueError("AgentEngine: 'response_parser' é obrigatório.")
        if action_executor is None:
            raise ValueError("AgentEngine: 'action_executor' é obrigatório.")

        self._context_builder = context_builder
        self._llm_executor = llm_executor
        self._response_parser = response_parser
        self._action_executor = action_executor

    # -------------------------
    # Propriedades de acesso (públicas, sem setters)
    # -------------------------

    @property
    def context_builder(self) -> ContextBuilder:
        return self._context_builder

    @property
    def llm_executor(self) -> LLMExecutor:
        return self._llm_executor

    @property
    def response_parser(self) -> ResponseParser:
        return self._response_parser

    @property
    def action_executor(self) -> ActionExecutor:
        return self._action_executor

    # -------------------------
    # Ciclo principal
    # -------------------------

    def execute(
        self,
        *,
        mission: Any,
        workspace: Any,
        user_instruction: str,
    ) -> AgentResult:
        """
        Executa o ciclo completo do agente.

        Args:
            mission: Missão atual (deve ter 'objective').
            workspace: Workspace atual (deve ter 'get_tree()' e 'is_open').
            user_instruction: Instrução do usuário.

        Returns:
            AgentResult com o resultado de cada etapa do ciclo.
        """
        # -------------------------
        # Validação de entradas
        # -------------------------
        if mission is None:
            return AgentResult(
                success=False,
                error="AgentEngine: 'mission' é obrigatório.",
            )
        if workspace is None:
            return AgentResult(
                success=False,
                error="AgentEngine: 'workspace' é obrigatório.",
            )
        if not user_instruction:
            return AgentResult(
                success=False,
                error="AgentEngine: 'user_instruction' é obrigatório.",
            )

        # -------------------------
        # Etapa 1: ContextBuilder
        # -------------------------
        try:
            objective = getattr(mission, "objective", None)
            if not objective:
                return AgentResult(
                    success=False,
                    error="AgentEngine: 'mission.objective' é obrigatório.",
                )

            project_tree = workspace.get_tree()
            project_root = project_tree.root

            context_result = self._context_builder.incremental_build(
                project=project_root,
                objective=objective,
            )
        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"AgentEngine: falha no ContextBuilder: {exc}",
            )

        # -------------------------
        # Etapa 2: LLMExecutor
        # -------------------------
        try:
            llm_result = self._llm_executor.execute(
                mission=mission,
                context_builder_result=context_result,
                workspace=workspace,
                user_instruction=user_instruction,
            )
        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"AgentEngine: falha no LLMExecutor: {exc}",
            )

        if not llm_result.success:
            return AgentResult(
                success=False,
                llm_response=(
                    llm_result.response.content if llm_result.response else None
                ),
                error=llm_result.error,
            )

        llm_response = llm_result.response

        # -------------------------
        # Etapa 3: ResponseParser
        # -------------------------
        try:
            parse_result = self._response_parser.parse(llm_response)
        except Exception as exc:
            return AgentResult(
                success=False,
                llm_response=(llm_response.content if llm_response else None),
                error=f"AgentEngine: falha no ResponseParser: {exc}",
            )

        if not parse_result.success:
            # LLM respondeu, mas a resposta não é uma Action estruturada
            # (apenas resposta textual). Não é um erro — apenas não há Action.
            return AgentResult(
                success=True,
                llm_response=llm_response.content if llm_response else None,
                action=None,
                execution_result=None,
                error=None,
            )

        action = parse_result.action

        # -------------------------
        # Etapa 4: ActionExecutor
        # -------------------------
        try:
            execution_result = self._action_executor.execute(action)
        except Exception as exc:
            return AgentResult(
                success=False,
                llm_response=llm_response.content if llm_response else None,
                action=action,
                error=f"AgentEngine: falha no ActionExecutor: {exc}",
            )

        success = bool(execution_result.get("success", False))

        return AgentResult(
            success=success,
            llm_response=llm_response.content if llm_response else None,
            action=action,
            execution_result=execution_result,
            error=execution_result.get("error") if not success else None,
        )
