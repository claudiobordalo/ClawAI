from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .goal import Goal


class GoalDependencyGraph:
    def __init__(self, goals: Tuple[Goal, ...]) -> None:
        self._goals = {g.id: g for g in goals}
        self._build_graph()

    def _build_graph(self) -> None:
        self._adj: Dict[str, List[str]] = {
            g.id: list(g.depends_on) for g in self._goals.values()
        }
        self._reverse_adj: Dict[str, List[str]] = {}
        for gid in self._goals:
            self._reverse_adj.setdefault(gid, [])
        for gid, deps in self._adj.items():
            for dep in deps:
                self._reverse_adj.setdefault(dep, []).append(gid)

    def has_cycle(self) -> bool:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {gid: WHITE for gid in self._goals}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for dep in self._adj.get(node, []):
                if dep not in color:
                    continue
                if color[dep] == GRAY:
                    return True
                if color[dep] == WHITE and dfs(dep):
                    return True
            color[node] = BLACK
            return False

        for gid in self._goals:
            if color[gid] == WHITE:
                if dfs(gid):
                    return True
        return False

    def find_cycle(self) -> List[str]:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {gid: WHITE for gid in self._goals}
        parent: Dict[str, Optional[str]] = {gid: None for gid in self._goals}
        cycle: List[str] = []

        def dfs(node: str) -> bool:
            nonlocal cycle
            color[node] = GRAY
            for dep in self._adj.get(node, []):
                if dep not in color:
                    continue
                if color[dep] == GRAY:
                    cur: str = node
                    while cur != dep:
                        cycle.append(cur)
                        cur = parent.get(cur) or ""
                    cycle.append(dep)
                    cycle.append(node)
                    cycle.reverse()
                    return True
                if color[dep] == WHITE:
                    parent[dep] = node
                    if dfs(dep):
                        return True
            color[node] = BLACK
            return False

        for gid in self._goals:
            if color[gid] == WHITE:
                if dfs(gid):
                    break
        return cycle

    def topological_sort(self) -> Tuple[Goal, ...]:
        if self.has_cycle():
            return tuple()

        in_degree: Dict[str, int] = {gid: 0 for gid in self._goals}
        for gid, deps in self._adj.items():
            in_degree[gid] = len([d for d in deps if d in self._goals])

        queue: deque = deque()
        for gid, degree in in_degree.items():
            if degree == 0:
                queue.append(gid)

        result: List[str] = []
        while queue:
            node = queue.popleft()
            result.append(node)
            for successor in self._reverse_adj.get(node, []):
                if successor in in_degree:
                    in_degree[successor] -= 1
                    if in_degree[successor] == 0:
                        queue.append(successor)

        return tuple(self._goals[gid] for gid in result if gid in self._goals)

    def get_unblocked(self) -> Tuple[Goal, ...]:
        unblocked: List[Goal] = []
        for g in self._goals.values():
            blocked = any(
                dep not in self._goals
                or str(self._goals[dep].status) not in ("done", "cancelled")
                for dep in g.depends_on
            )
            if not blocked:
                unblocked.append(g)
        return tuple(unblocked)

    def get_dependents(self, goal_id: str) -> Tuple[str, ...]:
        return tuple(self._reverse_adj.get(goal_id, []))

    def dependency_depth(self, goal_id: str) -> int:
        visited: Set[str] = set()

        def dfs(node: str) -> int:
            if node in visited:
                return 0
            visited.add(node)
            max_depth = 0
            for dep in self._adj.get(node, []):
                if dep in self._goals:
                    max_depth = max(max_depth, 1 + dfs(dep))
            return max_depth

        return dfs(goal_id)
