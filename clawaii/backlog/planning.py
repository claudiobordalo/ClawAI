from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .backlog import BacklogManager

BACKLOG_DIR = Path(__file__).resolve().parent
ROADMAP_PATH = BACKLOG_DIR / "roadmap.json"


def generate_roadmap(backlog: BacklogManager) -> dict:
    """Generates a roadmap based on the current backlog."""
    open_items = backlog.get_open_items()
    high_priority = [item for item in open_items if item.priority <= 2]
    medium_priority = [item for item in open_items if item.priority == 3]
    low_priority = [item for item in open_items if item.priority >= 4]

    roadmap = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phases": [
            {
                "id": "phase-1",
                "name": "Critical Fixes",
                "items": [item.id for item in high_priority],
                "description": "High priority issues and critical failures."
            },
            {
                "id": "phase-2",
                "name": "Improvements",
                "items": [item.id for item in medium_priority],
                "description": "Medium priority improvements and refactors."
            },
            {
                "id": "phase-3",
                "name": "Enhancements",
                "items": [item.id for item in low_priority],
                "description": "Low priority enhancements and nice-to-haves."
            }
        ]
    }
    return roadmap


def save_roadmap(roadmap: dict) -> None:
    """Saves the roadmap to a JSON file."""
    ROADMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROADMAP_PATH.write_text(json.dumps(roadmap, ensure_ascii=False, indent=2), encoding="utf-8")


def run_auto_planning(backlog: BacklogManager) -> dict:
    """Runs planning and saves the roadmap."""
    roadmap = generate_roadmap(backlog)
    save_roadmap(roadmap)
    return roadmap
