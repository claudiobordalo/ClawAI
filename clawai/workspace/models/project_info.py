from __future__ import annotations

from dataclasses import dataclass, field

from clawai.workspace.models.project_file import ProjectFile


@dataclass(slots=True)
class ProjectInfo:

    name: str
    root: str

    files: list[ProjectFile] = field(default_factory=list)
    languages: set[str] = field(default_factory=set)
