from __future__ import annotations

from dataclasses import dataclass

from clawai.mission.mission_executor import MissionExecutor
from clawai.mission.mission import Mission
from clawai.mission.mission_step import MissionStep
from clawai.mission.agent_executor import AgentExecutor
from clawai.mission.mission_state import MissionStatus, MissionStepStatus


class FakeExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str]] = []

    def execute_step(self, *, step: MissionStep, mission: Mission) -> dict[str, object]:
        self.calls.append((mission.current_step, step.description))
        return {
            "operations": [{"path": "x", "type": "delete"}],
        }


def test_mission_executor_happy_path_records_history() -> None:
    mission = Mission(id="m1", objective="obj", priority=1)
    mission.steps = [
        MissionStep(
            description="patch_generation",
            status=MissionStepStatus.created.value,
            dependencies=[],
        )
    ]

    executor: AgentExecutor = FakeExecutor()  # type: ignore[assignment]
    mission_executor = MissionExecutor(mission=mission, executor=executor)

    out = mission_executor.run()

    assert out.status == MissionStatus.completed
    assert out.current_step == 0
    assert len(out.steps) == 1
    # MissionExecutor marca step como completed ao validar
    assert out.steps[0].status == MissionStepStatus.completed.value

    # Deve registrar eventos principais
    events = [h["event"] for h in out.history]
    assert "planning" in events
    assert "step_running" in events
    assert "step_validated" in events
    assert "mission_validated" in events
    assert "history_registered" in events
    assert "mission_finalized" in events

    # Garantia de que executou exatamente 1 etapa
    assert len(executor.calls) == 1
