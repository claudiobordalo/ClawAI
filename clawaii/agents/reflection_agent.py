from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentState:

    objective: str

    observation: str = ""

    reasoning: str = ""

    next_action: str = ""

    finished: bool = False

    iteration: int = 0


class ReflectionAgent:

    def reflect(
        self,
        state: AgentState,
    ) -> AgentState:

        observation = state.observation.lower()

        state.iteration += 1

        if "traceback" in observation:

            state.reasoning = (
                "Foi detectada uma exceção Python."
            )

            state.next_action = (
                "Investigar arquivos envolvidos no traceback."
            )

            return state

        if "error" in observation:

            state.reasoning = (
                "Foi detectado um erro."
            )

            state.next_action = (
                "Localizar origem do erro e gerar patch."
            )

            return state

        if "failed" in observation:

            state.reasoning = (
                "Foi detectada uma falha de execução."
            )

            state.next_action = (
                "Executar nova análise."
            )

            return state

        state.reasoning = (
            "Nenhum erro encontrado."
        )

        state.next_action = (
            "Finalizar tarefa."
        )

        state.finished = True

        return state


reflection_agent = ReflectionAgent()
