from __future__ import annotations

import json

from clawai.ai.router import AIRouter
from clawai.tools.tool_executor import tool_executor


class AgentLoop:

    def __init__(self) -> None:

        self.router = AIRouter()

    def run(
        self,
        prompt: str,
        max_steps: int = 15,
    ) -> str:

        history = []

        for _ in range(max_steps):

            full_prompt = f"""
Você é o agente do ClawAI.

Você pode responder de DUAS formas.

Forma 1:

Responder normalmente ao usuário.

Forma 2:

Solicitar uma ferramenta.

Formato obrigatório:

{{
    "tool":"read_file",
    "arguments":{{...}}
}}

Ferramentas:

read_file

write_file

list_directory

search_project

Histórico:

{history}

Pedido:

{prompt}

Caso já tenha informações suficientes,
responda normalmente.
"""

            answer = self.router.ask(full_prompt)

            answer = answer.strip()

            if not answer.startswith("{"):

                return answer

            call = json.loads(answer)

            result = tool_executor.execute_json(
                json.dumps(call)
            )

            history.append(
                {
                    "tool": call,
                    "result": result,
                }
            )

        return "Limite de passos atingido."


agent_loop = AgentLoop()
