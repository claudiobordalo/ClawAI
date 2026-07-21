from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from clawai.mission.agent_executor import AgentExecutor
from clawai.mission.mission import Mission
from clawai.mission.mission_state import MissionStepStatus, MissionStatus
from clawai.mission.mission_step import MissionStep
from clawai.resources.manager import ResourceManager
from clawai.ai.router import ModelRouter

if TYPE_CHECKING:
    from clawai.dispatcher.dispatcher import Dispatcher


class _ExecutorDispatcherAdapter:
    """
    Adapter que expõe a interface de Dispatcher, delegando para um AgentExecutor.
    Mantém compatibilidade com testes existentes sem acoplar MissionExecutor a agentes concretos.
    """

    def __init__(
        self,
        *,
        executor: AgentExecutor,
        resource_manager: ResourceManager,
        model_router: ModelRouter,
    ) -> None:
        self._executor = executor
        self._resource_manager = resource_manager
        self._model_router = model_router

    def dispatch(self, *, mission: Mission, resource_manager: ResourceManager, model_router: ModelRouter) -> dict[str, Any]:
        idx = mission.current_step
        step = mission.steps[idx]
        return self._executor.execute_step(step=step, mission=mission)


class MissionExecutor:
    def __init__(
        self,
        *,
        mission: Mission,
        dispatcher: Dispatcher | None = None,
        executor: AgentExecutor | None = None,
        resource_manager: ResourceManager | None = None,
        model_router: ModelRouter | None = None,
    ) -> None:
        """
        MissionExecutor passa a depender apenas de Dispatcher.

        Compatibilidade: se `executor` for fornecido, criamos um dispatcher adapter
        que chama o executor diretamente.
        """
        self._mission = mission
        self._resource_manager = resource_manager or ResourceManager()
        self._model_router = model_router or ModelRouter()
        self._dispatcher = dispatcher

        if self._dispatcher is None:
            if executor is None:
                raise ValueError("Informe `dispatcher` ou `executor`.")
            self._dispatcher = _ExecutorDispatcherAdapter(
                executor=executor,
                resource_manager=self._resource_manager,
                model_router=self._model_router,
            )

    @property
    def mission(self) -> Mission:
        return self._mission

    def _record_history(self, *, event: str, **extra: Any) -> None:
        self._mission.history.append(
            {
                "event": event,
                "mission_id": self._mission.id,
                "current_step": self._mission.current_step,
                **extra,
            }
        )

    def planejar(self) -> None:
        if not self._mission.steps:
            # fallback: 1 etapa padrão
            self._mission.steps = [
                MissionStep(
                    description="patch_generation",
                    status=MissionStepStatus.created.value,
                    dependencies=[],
                )
            ]
        self._mission.status = MissionStatus.planning
        self._record_history(
            event="planning",
            steps=len(self._mission.steps),
        )

    def executar(self) -> None:
        self._mission.status = MissionStatus.running
        for idx, step in enumerate(self._mission.steps):
            self._mission.current_step = idx

            # step start
            step.status = MissionStepStatus.running.value
            self._record_history(
                event="step_running",
                step_idx=idx,
                step=asdict(step),
            )

            try:
                payload = self._dispatcher.dispatch(
                    mission=self._mission,
                    resource_manager=self._resource_manager,
                    model_router=self._model_router,
                )

                self._mission.context.update(
                    {
                        "step_payload": payload,
                    }
                )
                self._mission.result.update(
                    {
                        "step_result": payload,
                    }
                )

                # step validate
                step.status = MissionStepStatus.completed.value
                self._record_history(
                    event="step_validated",
                    step_idx=idx,
                    step_status=step.status,
                )

            except Exception as exc:  # pragma: no cover
                step.status = MissionStepStatus.failed.value
                self._mission.status = MissionStatus.failed
                self._record_history(
                    event="step_failed",
                    step_idx=idx,
                    error=str(exc),
                )
                raise

    def validar(self) -> None:
        # etapa única por sprint: valida no final
        if self._mission.status == MissionStatus.failed:
            return
        self._mission.status = MissionStatus.completed
        self._record_history(event="mission_validated")

    def registrar_historico(self) -> None:
        # já registramos incrementalmente; este método existe por clareza do fluxo
        self._record_history(event="history_registered")

    def proxima_etapa(self) -> None:
        # se houver passos, a execução já percorreu tudo.
        self._mission.current_step = max(0, len(self._mission.steps) - 1)

    def finalizar(self) -> None:
        if self._mission.status != MissionStatus.failed:
            self._mission.status = MissionStatus.completed
        self._record_history(event="mission_finalized", status=self._mission.status.value)

    def run(self) -> Mission:
        if not self._mission.id:
            self._mission.id = str(uuid4())

        self.planejar()
        self.executar()
        self.validar()
        self.registrar_historico()
        self.proxima_etapa()
        self.finalizar()
        return self._mission
