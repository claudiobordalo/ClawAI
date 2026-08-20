from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from clawai.engineering import AbstractMemory, MemoryQuery

from .goal import Goal
from .goal_backlog import GoalBacklog
from .goal_events import (
    GOAL_CANCELLED,
    GOAL_COMPLETED,
    GOAL_CREATED,
    GOAL_FAILED,
    GOAL_PROGRESS_UPDATED,
    GoalEventBus,
)
from .goal_priority import GoalPriority
from .goal_progress import GoalProgress
from .goal_repository import GoalRepository
from .goal_status import GoalStatus
from .abstract_goal_manager import AbstractGoalManager
from .goal_validator import validate_goal

logger = logging.getLogger("clawai.goals")


def _failed_count_to_priority(n: int) -> GoalPriority:
    if n >= 2:
        return GoalPriority.CRITICAL
    if n == 1:
        return GoalPriority.HIGH
    return GoalPriority.MEDIUM


class GoalManager(AbstractGoalManager):
    def __init__(
        self,
        repository: GoalRepository,
        event_bus: Optional[GoalEventBus] = None,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus or GoalEventBus()
        self._backlog: Optional[GoalBacklog] = None

    def _load_memory(self) -> Optional[AbstractMemory]:
        if hasattr(self._repository, "_engineering_memory"):
            return self._repository._engineering_memory
        return None

    def create_backlog(self) -> GoalBacklog:
        all_goals = list(self._repository.list())
        memory = self._load_memory()
        if memory is not None:
            all_goals = self._merge_with_memory_goals(all_goals, memory)

        seen: set[str] = set()
        deduped: List[Goal] = []
        for g in all_goals:
            key = g.title.strip().lower()
            if key not in seen:
                seen.add(key)
                deduped.append(g)

        deduped.sort(key=lambda g: (int(g.priority), g.title.lower(), g.id))
        now = datetime.now(timezone.utc)
        self._backlog = GoalBacklog(
            goals=tuple(deduped),
            created_at=now,
            summary=f"Backlog with {len(deduped)} goals",
        )
        return self._backlog

    def _merge_with_memory_goals(
        self, existing: List[Goal], memory: AbstractMemory
    ) -> List[Goal]:
        result = memory.query(MemoryQuery())
        records = result.records

        seen_titles = {g.title.strip().lower() for g in existing}

        groups: Dict[str, list] = {}
        for r in records:
            key = r.objective.strip().lower()
            if key in seen_titles:
                continue
            if key not in groups:
                groups[key] = []
            groups[key].append(r)

        new_goals: List[Goal] = []
        for key, recs in groups.items():
            all_succeeded = all(r.success for r in recs)
            goal_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"clawai.goal.{key}"))
            if all_succeeded:
                new_goals.append(
                    Goal(
                        id=goal_id,
                        title=recs[0].objective,
                        description=recs[-1].diagnosis,
                        success_criteria=recs[-1].summary,
                        priority=GoalPriority.MEDIUM,
                        status=GoalStatus.DONE,
                    )
                )
            else:
                failed_count = sum(1 for r in recs if not r.success)
                new_goals.append(
                    Goal(
                        id=goal_id,
                        title=recs[0].objective,
                        description=recs[-1].diagnosis,
                        success_criteria=recs[-1].summary,
                        priority=_failed_count_to_priority(failed_count),
                        status=GoalStatus.TODO,
                    )
                )

        for g in new_goals:
            self._repository.save(g)
            self._event_bus.emit(
                GOAL_CREATED, g.id, title=g.title, priority=int(g.priority)
            )

        return existing + new_goals

    def next_goal(self) -> Optional[Goal]:
        if self._backlog is None:
            self.create_backlog()
        if self._backlog is None or not self._backlog.goals:
            return None
        for g in self._backlog.goals:
            if g.status == GoalStatus.TODO:
                logger.info(
                    "Next goal selected",
                    extra={"goal_id": g.id, "title": g.title, "status": g.status.value},
                )
                return g
        return None

    def add_goal(self, goal: Goal) -> Goal:
        existing = self._repository.list()
        validate_goal(goal, existing_goals=existing)
        self._repository.save(goal)
        self._event_bus.emit(
            GOAL_CREATED, goal.id, title=goal.title, priority=int(goal.priority)
        )
        self._invalidate_backlog()
        logger.info(
            "Goal added",
            extra={
                "goal_id": goal.id,
                "title": goal.title,
                "priority": int(goal.priority),
            },
        )
        return goal

    def complete_goal(self, goal_id: str) -> Optional[Goal]:
        goal = self._repository.load(goal_id)
        if goal is None:
            return None
        updated = Goal(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            success_criteria=goal.success_criteria,
            priority=goal.priority,
            status=GoalStatus.DONE,
        )
        self._repository.update(updated)
        self._invalidate_backlog()
        self._event_bus.emit(GOAL_COMPLETED, goal_id, title=goal.title)
        logger.info("Goal completed", extra={"goal_id": goal_id, "title": goal.title})
        return updated

    def fail_goal(self, goal_id: str) -> Optional[Goal]:
        goal = self._repository.load(goal_id)
        if goal is None:
            return None
        updated = Goal(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            success_criteria=goal.success_criteria,
            priority=goal.priority,
            status=GoalStatus.BLOCKED,
        )
        self._repository.update(updated)
        self._invalidate_backlog()
        self._event_bus.emit(
            GOAL_FAILED, goal_id, title=goal.title, status="blocked"
        )
        logger.info("Goal blocked", extra={"goal_id": goal_id, "title": goal.title})
        return updated

    def reprioritize(
        self, goal_id: str, new_priority: GoalPriority | int
    ) -> Optional[Goal]:
        goal = self._repository.load(goal_id)
        if goal is None:
            return None
        if not isinstance(new_priority, GoalPriority):
            new_priority = GoalPriority(int(new_priority))
        updated = Goal(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            success_criteria=goal.success_criteria,
            priority=new_priority,
            status=goal.status,
        )
        self._repository.update(updated)
        self._invalidate_backlog()
        logger.info(
            "Goal reprioritized",
            extra={"goal_id": goal_id, "new_priority": new_priority.value},
        )
        return updated

    def find_goal(self, goal_id: str) -> Optional[Goal]:
        return self._repository.load(goal_id)

    def remove_goal(self, goal_id: str) -> bool:
        goal = self._repository.load(goal_id)
        if goal is None:
            return False
        self._repository.delete(goal_id)
        self._invalidate_backlog()
        self._event_bus.emit(
            GOAL_CANCELLED, goal_id, title=goal.title if goal else "unknown"
        )
        logger.info("Goal removed", extra={"goal_id": goal_id})
        return True

    def update_progress(
        self, goal_id: str, completion: float
    ) -> Optional[GoalProgress]:
        goal = self._repository.load(goal_id)
        if goal is None:
            return None
        goal_progress = GoalProgress(
            goal=goal,
            completion=completion,
            completed_items=(goal.title,) if completion >= 100.0 else tuple(),
            remaining_items=tuple() if completion >= 100.0 else (goal.title,),
            summary=f"{completion:.1f}% complete",
        )
        self._event_bus.emit(
            GOAL_PROGRESS_UPDATED,
            goal_id,
            completion=completion,
            title=goal.title,
        )
        if completion >= 100.0 and goal.status != GoalStatus.DONE:
            self.complete_goal(goal_id)
        logger.info(
            "Goal progress updated",
            extra={"goal_id": goal_id, "completion": completion},
        )
        return goal_progress

    def progress(self) -> GoalProgress:
        if self._backlog is None or not self._backlog.goals:
            self.create_backlog()
        if self._backlog is None or not self._backlog.goals:
            return GoalProgress(
                goal=None,
                completion=0.0,
                completed_items=tuple(),
                remaining_items=tuple(),
                summary="No goals in backlog",
            )
        goals = self._backlog.goals
        total = len(goals)
        completed = sum(1 for g in goals if g.status == GoalStatus.DONE)
        completion = (completed / total) * 100.0 if total > 0 else 0.0
        completed_items = tuple(g.title for g in goals if g.status == GoalStatus.DONE)
        remaining_items = tuple(g.title for g in goals if g.status != GoalStatus.DONE)
        first_pending = self.next_goal()
        return GoalProgress(
            goal=first_pending,
            completion=completion,
            completed_items=completed_items,
            remaining_items=remaining_items,
            summary=f"{completed}/{total} goals completed ({completion:.1f}%)",
        )

    def _invalidate_backlog(self) -> None:
        self._backlog = None
