from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from clawai.cognition import AbstractReasoningEngine
from clawai.engineering import AbstractMemory
from clawai.executor import AbstractExecutor
from clawai.goals import AbstractGoalManager, AbstractPlanner, GoalEventBus

from .abstract_agent_loop import AbstractAgentLoop
from .abstract_checkpoint_manager import AbstractCheckpointManager
from .execution_session import ExecutionSession
from .retry_policy import RetryPolicy


@dataclass
class AgentConfiguration:
    max_goals: int = 0
    auto_replan: bool = True
    checkpoint_enabled: bool = False
    checkpoint_dir: str = ".checkpoints"


@dataclass
class AgentContext:
    planner: AbstractPlanner
    goal_manager: AbstractGoalManager
    executor: AbstractExecutor
    memory: AbstractMemory
    event_bus: GoalEventBus
    reasoning_engine: AbstractReasoningEngine
    retry_policy: RetryPolicy
    config: AgentConfiguration
    agent_loop: Optional[AbstractAgentLoop] = None
    checkpoint_manager: Optional[AbstractCheckpointManager] = None
    session: Optional[ExecutionSession] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
