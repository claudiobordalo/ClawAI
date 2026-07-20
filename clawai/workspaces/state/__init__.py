# clawai/workspaces/state/__init__.py
"""Re-export workspace state for use by API routers and other modules.

This module exists solely to provide a stable import path:
    from clawai.workspaces.state import workspace_state
"""
from ..manager import WorkspaceInfo, WorkspaceManager, workspace_manager

workspace_state = workspace_manager

__all__ = [
    "WorkspaceInfo",
    "WorkspaceManager",
    "workspace_manager",
    "workspace_state",
]
