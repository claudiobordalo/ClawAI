from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

from .goal import Goal
from .goal_dependency_graph import GoalDependencyGraph
from .goal_priority import GoalPriority


class ValidationError(Exception):
    def __init__(self, message: str, errors: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.errors = errors or []


_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")
_VALID_TAGS = frozenset(
    {
        "backend",
        "frontend",
        "tests",
        "docs",
        "security",
        "performance",
        "devops",
        "infra",
        "refactor",
        "bugfix",
        "feature",
        "research",
    }
)


def validate_goal(
    goal: Goal,
    existing_goals: Sequence[Goal] = (),
) -> None:
    errors: List[str] = []

    if not goal.id or not goal.id.strip():
        errors.append("Goal id must not be empty")

    if not _ID_PATTERN.match(goal.id):
        errors.append(
            f"Invalid goal id: {goal.id!r}. " f"Must match {_ID_PATTERN.pattern}"
        )

    if not goal.title or not goal.title.strip():
        errors.append("Goal title must not be empty")

    if not goal.success_criteria or not goal.success_criteria.strip():
        errors.append("Goal success_criteria must not be empty")

    if not isinstance(goal.priority, GoalPriority):
        try:
            GoalPriority(goal.priority)
        except (ValueError, TypeError):
            errors.append(
                f"Invalid priority: {goal.priority!r}. "
                f"Must be a GoalPriority or compatible int"
            )

    for tag in goal.tags:
        if tag not in _VALID_TAGS:
            errors.append(
                f"Invalid tag: {tag!r}. " f"Must be one of {sorted(_VALID_TAGS)}"
            )

    for existing in existing_goals:
        if existing.id == goal.id:
            continue
        if existing.title.strip().lower() == goal.title.strip().lower():
            errors.append(
                f"Duplicate goal title: {goal.title!r} "
                f"(already exists as {existing.id})"
            )

    if errors:
        raise ValidationError(
            f"Goal validation failed ({len(errors)} error(s))",
            errors=errors,
        )


def validate_backlog(goals: Tuple[Goal, ...]) -> None:
    errors: List[str] = []

    if not goals:
        errors.append("Backlog must not be empty")

    graph = GoalDependencyGraph(goals)

    if graph.has_cycle():
        cycle = graph.find_cycle()
        errors.append(f"Backlog contains a dependency cycle: {' -> '.join(cycle)}")

    goal_ids = {g.id for g in goals}
    for g in goals:
        for dep_id in g.depends_on:
            if dep_id not in goal_ids:
                errors.append(f"Goal {g.id!r} depends on non-existent goal {dep_id!r}")

    seen_titles: set[str] = set()
    for g in goals:
        key = g.title.strip().lower()
        if key in seen_titles:
            errors.append(f"Duplicate goal title: {g.title!r}")
        seen_titles.add(key)

    if errors:
        raise ValidationError(
            f"Backlog validation failed ({len(errors)} error(s))",
            errors=errors,
        )
