from __future__ import annotations

import logging
from typing import Optional

from clawai.cognition import AbstractReasoningEngine, CognitiveFactory
from clawai.engineering import AbstractMemory
from clawai.executor import AbstractExecutor
from clawai.goals import AbstractGoalManager, GoalEventBus

from .abstract_autonomous_agent import AbstractAutonomousAgent
from .abstract_agent_loop import AbstractAgentLoop
from .abstract_agent_loop import AbstractAgentLoop as _AbstractAgentLoop
from .abstract_checkpoint_manager import AbstractCheckpointManager
from .agent_context import AgentConfiguration, AgentContext
from .execution_session import ExecutionSession
from .retry_policy import RetryPolicy

logger = logging.getLogger("clawai.agent")


class AutonomousAgent(AbstractAutonomousAgent):
    def __init__(
        self,
        planner=None,
        goal_manager: Optional[AbstractGoalManager] = None,
        executor: Optional[AbstractExecutor] = None,
        memory: Optional[AbstractMemory] = None,
        event_bus: Optional[GoalEventBus] = None,
        reasoning_engine: Optional[AbstractReasoningEngine] = None,
        retry_policy: Optional[RetryPolicy] = None,
        config: Optional[AgentConfiguration] = None,
        context: Optional[AgentContext] = None,
        agent_loop: Optional[AbstractAgentLoop] = None,
        checkpoint_manager: Optional[AbstractCheckpointManager] = None,
    ) -> None:
        if context is not None:
            self._context = context
        else:
            self._context = AgentContext(
                planner=planner,
                goal_manager=goal_manager,
                executor=executor,
                memory=memory,
                event_bus=event_bus or GoalEventBus(),
                reasoning_engine=reasoning_engine or CognitiveFactory().create_reasoning_engine(),
                retry_policy=retry_policy or RetryPolicy(),
                config=config or AgentConfiguration(),
                checkpoint_manager=checkpoint_manager,
            )

        # Canonical behavior: always create/use an AgentLoop from the context
        # unless one was explicitly provided.
        self._loop: Optional[AbstractAgentLoop] = agent_loop or AbstractAgentLoop.create_default(
            self._context
        )

    @property
    def context(self) -> AgentContext:
        return self._context

    @property
    def loop(self) -> Optional[AbstractAgentLoop]:
        return self._loop

    def run(self, objective: str) -> ExecutionSession:
        if self._loop is None:
            msg = "AgentLoop not provided. Pass agent_loop= to constructor or use AgentContext with agent_loop."
            raise RuntimeError(msg)
        return self._loop.run(objective)

    def cancel(self) -> None:
        if self._loop:
            self._loop.cancel()

    def pause(self) -> None:
        if self._loop:
            self._loop.pause()

    def resume(self) -> None:
        if self._loop:
            self._loop.resume()

    def stop(self) -> None:
        if self._loop:
            self._loop.stop()
