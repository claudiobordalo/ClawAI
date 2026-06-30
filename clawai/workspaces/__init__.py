# clawai/workspaces/__init__.py
from .manager import WorkspaceInfo, WorkspaceManager, workspace_manager

workspace_state = workspace_manager

__all__ = [
    "WorkspaceInfo",
    "WorkspaceManager",
    "workspace_manager",
    "workspace_state",
]