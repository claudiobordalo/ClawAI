from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:

    def __init__(self) -> None:

        self.root = Path(".clawai/backups")

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def backup(
        self,
        project: str | Path,
        file: str | Path,
    ) -> Path:

        project = Path(project)
        source = project / file

        if not source.exists():
            return Path()

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        destination = (
            self.root /
            timestamp /
            file
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )

        return destination

    def restore(
        self,
        backup: str | Path,
        project: str | Path,
    ) -> None:

        backup = Path(backup)

        target = (
            Path(project) /
            backup.relative_to(self.root).parts[1]
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            backup,
            target,
        )


backup_manager = BackupManager()
