from __future__ import annotations

import uuid
from pathlib import Path

from clawai.projects.models.project import Project
from clawai.storage.services.storage_manager import StorageManager


class ProjectManager:

    STORAGE_KEY = "projects/projects"

    def __init__(
        self,
        storage: StorageManager,
    ) -> None:

        self._storage = storage

    def create(
        self,
        name: str,
        path: str | Path,
    ) -> Project:

        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            path=Path(path).resolve(),
        )

        projects = self.list()

        projects.append(project)

        self._save(projects)

        return project

    def list(
        self,
    ) -> list[Project]:

        data = self._storage.load(self.STORAGE_KEY)

        if not data:
            return []

        return [
            Project(
                id=item["id"],
                name=item["name"],
                path=Path(item["path"]),
            )
            for item in data
        ]

    def get(
        self,
        name: str,
    ) -> Project | None:

        for project in self.list():

            if project.name.lower() == name.lower():
                return project

        return None

    def delete(
        self,
        project_id: str,
    ) -> bool:

        projects = [
            p
            for p in self.list()
            if p.id != project_id
        ]

        self._save(projects)

        return True

    def _save(
        self,
        projects: list[Project],
    ) -> None:

        self._storage.save(
            self.STORAGE_KEY,
            [
                {
                    "id": p.id,
                    "name": p.name,
                    "path": str(p.path),
                }
                for p in projects
            ],
        )
