from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from clawai.goals import GoalBacklog

from .abstract_checkpoint_manager import AbstractCheckpointManager
from .execution_session import ExecutionSession


class CheckpointManager(AbstractCheckpointManager):
    def __init__(self, checkpoint_dir: str = ".checkpoints") -> None:
        self._checkpoint_dir = checkpoint_dir

    def _ensure_dir(self) -> None:
        os.makedirs(self._checkpoint_dir, exist_ok=True)

    def _checkpoint_path(self, session_id: str) -> str:
        return os.path.join(self._checkpoint_dir, f"{session_id}.json")

    def save(
        self,
        session: ExecutionSession,
        backlog: Optional[GoalBacklog] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        self._ensure_dir()
        path = self._checkpoint_path(session.id)
        data: Dict[str, Any] = {
            "session_id": session.id,
            "objective": session.objective,
            "state": session.state.value,
            "current_goal": session.current_goal,
            "completed_goals": session.completed_goals,
            "failed_goals": session.failed_goals,
            "cancelled": session.cancelled,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if backlog is not None:
            data["backlog_goal_ids"] = [g.id for g in backlog.goals]
        if extra:
            data.update(extra)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = self._checkpoint_path(session_id)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    def delete(self, session_id: str) -> bool:
        path = self._checkpoint_path(session_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
