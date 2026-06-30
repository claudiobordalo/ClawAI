from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

@dataclass
class Workspace:
    workspace_id: str
    name: str
    root: str
    active: bool = False

workspace = Workspace("default", ROOT.name, str(ROOT), True)
