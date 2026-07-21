from __future__ import annotations

from typing import Any, Protocol

from clawai.mission.mission_step import MissionStep


class AgentExecutor(Protocol):
    def execute_step(
        self,
        *,
        step: MissionStep,
        mission: Any,
    ) -> dict[str, Any]:
        """
        Executa a etapa e retorna um dict com dados para persistir em mission.context/mission.result.
        """
        ...
