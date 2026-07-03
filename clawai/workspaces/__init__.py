# clawai/workspaces/__init__.py
from .analyzer import ProjectAnalyzer, ProjectMap
from .manager import WorkspaceInfo, WorkspaceManager, workspace_manager

workspace_state = workspace_manager

__all__ = [
    "ProjectAnalyzer",
    "ProjectMap",
    "WorkspaceInfo",
    "WorkspaceManager",
    "workspace_manager",
    "workspace_state",
]
