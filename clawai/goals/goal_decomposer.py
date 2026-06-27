from __future__ import annotations

import re
from typing import List, Tuple

from .goal import Goal
from .goal_priority import GoalPriority
from .goal_status import GoalStatus


class GoalDecomposer:
    _BULLET_PATTERN = re.compile(r"^[\s]*[-*\u2022\u2023\u25E6\u2043\u2219]\s+")
    _NUMBERED_PATTERN = re.compile(r"^[\s]*\d+[\.\)]\s+")
    _AND_PATTERN = re.compile(r"\s+and\s+", re.IGNORECASE)

    def decompose(
        self, objective: str, goal_id_prefix: str = "plan"
    ) -> Tuple[Goal, ...]:
        raw_lines = self._split_objective(objective)
        if not raw_lines:
            return ()

        seen: set[str] = set()
        goals: List[Goal] = []

        import uuid

        for line in raw_lines:
            title = line.rstrip(".").strip()
            if not title:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            goal_id = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"clawai.{goal_id_prefix}.{key}")
            )
            goals.append(
                Goal(
                    id=goal_id,
                    title=title,
                    description=f"Decomposed from: {objective[:120]}",
                    success_criteria=f"{title} completed successfully",
                    priority=GoalPriority.MEDIUM,
                    status=GoalStatus.TODO,
                    estimated_complexity=self._infer_complexity(title),
                    tags=self._infer_tags(title),
                )
            )

        return tuple(goals)

    def _split_objective(self, objective: str) -> List[str]:
        if not objective or not objective.strip():
            return []

        lines = objective.split("\n")
        candidates: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            cleaned = self._BULLET_PATTERN.sub("", stripped)
            cleaned = self._NUMBERED_PATTERN.sub("", cleaned)
            candidates.append(cleaned)

        if len(candidates) >= 2:
            return candidates

        parts = self._AND_PATTERN.split(objective.strip())
        if len(parts) >= 2:
            return [p.strip().rstrip(".") for p in parts if p.strip()]

        return [objective.strip()]

    def _infer_complexity(self, title: str) -> str:
        lower = title.lower()
        if any(kw in lower for kw in ("simple", "tiny", "quick", "minor", "small")):
            return "XS"
        if any(kw in lower for kw in ("easy", "trivial", "cosmetic", "config")):
            return "S"
        if any(
            kw in lower for kw in ("large", "complex", "major", "big", "significant")
        ):
            return "L"
        if any(
            kw in lower for kw in ("huge", "massive", "enormous", "architect", "epic")
        ):
            return "XL"
        return "M"

    def _infer_tags(self, title: str) -> Tuple[str, ...]:
        lower = title.lower()
        tags: List[str] = []
        if any(
            kw in lower
            for kw in ("backend", "server", "api", "database", "db", "service")
        ):
            tags.append("backend")
        if any(kw in lower for kw in ("frontend", "ui", "ux", "client", "web")):
            tags.append("frontend")
        if any(kw in lower for kw in ("test", "spec", "coverage", "assert", "verify")):
            tags.append("tests")
        if any(kw in lower for kw in ("doc", "readme", "manual", "guide", "comment")):
            tags.append("docs")
        if any(
            kw in lower
            for kw in ("security", "auth", "oauth", "login", "permission", "encrypt")
        ):
            tags.append("security")
        if any(kw in lower for kw in ("perf", "speed", "latency", "optimize", "cache")):
            tags.append("performance")
        return tuple(tags)
