from __future__ import annotations

from typing import List, Optional, Tuple

from clawai.engineering import AbstractMemory
from clawai.goals import Goal, GoalBacklog, GoalEventBus, PlanningContext, GoalStatus
from clawai.goals.abstract_planner import AbstractPlanner


_REPLAN_STARTED = "cognition.replan_started"
_REPLAN_COMPLETED = "cognition.replan_completed"


class ReplanningEngine:
    def __init__(
        self,
        planner: AbstractPlanner,
        memory: Optional[AbstractMemory] = None,
        event_bus: Optional[GoalEventBus] = None,
    ) -> None:
        self._planner = planner
        self._memory = memory
        self._event_bus = event_bus

    def replan(
        self,
        objective: str,
        current_goals: Tuple[Goal, ...],
        previous_attempts: int = 0,
        context: Optional[str] = None,
    ) -> GoalBacklog:
        if self._event_bus:
            self._event_bus.emit(
                _REPLAN_STARTED, objective, previous_attempts=previous_attempts
            )

        ctx = PlanningContext(
            objective=objective,
            engineering_memory=self._memory,
            repository_state=list(current_goals),
            previous_attempts=previous_attempts,
        )
        backlog = self._planner.plan(objective, context=ctx)

        completed = {
            g.id
            for g in current_goals
            if g.status in (GoalStatus.DONE, GoalStatus.CANCELLED)
        }
        if completed:
            preserved: List[Goal] = [g for g in current_goals if g.id in completed]
            seen_ids = {g.id for g in backlog.goals}
            new_goals = [g for g in preserved if g.id not in seen_ids]
            all_goals = list(backlog.goals) + new_goals

            from datetime import datetime, timezone

            result = GoalBacklog(
                goals=tuple(all_goals),
                created_at=datetime.now(timezone.utc),
                summary=f"Replanned {len(all_goals)} goals ({len(preserved)} preserved)",
            )
        else:
            result = backlog

        if self._event_bus:
            self._event_bus.emit(
                _REPLAN_COMPLETED,
                objective,
                goal_count=len(result.goals),
            )

        return result
