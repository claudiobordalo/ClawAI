from __future__ import annotations

from pathlib import Path

from clawai.tools.base.tool import Tool


class FileSystemTool(Tool):

    @property
    def name(self) -> str:
        return "filesystem"

    def execute(
        self,
        action: str,
        **kwargs,
    ):

        actions = {
            "read": self.read,
            "write": self.write,
            "append": self.append,
            "delete": self.delete,
            "exists": self.exists,
            "mkdir": self.mkdir,
            "list": self.list,
            "copy": self.copy,
            "move": self.move,
        }

        if action not in actions:
            raise ValueError(f"Unknown action: {action}")

        return actions[action](**kwargs)

    def read(
        self,
        path: str,
    ) -> str:

        return Path(path).read_text(
            encoding="utf-8",
        )

    def write(
        self,
        path: str,
        content: str,
    ) -> None:

        file = Path(path)

        file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file.write_text(
            content,
            encoding="utf-8",
        )

    def append(
        self,
        path: str,
        content: str,
    ) -> None:

        Path(path).open(
            "a",
            encoding="utf-8",
        ).write(content)

    def delete(
        self,
        path: str,
    ) -> None:

        Path(path).unlink(
            missing_ok=True,
        )

    def exists(
        self,
        path: str,
    ) -> bool:

        return Path(path).exists()

    def mkdir(
        self,
        path: str,
    ) -> None:

        Path(path).mkdir(
            parents=True,
            exist_ok=True,
        )

    def list(
        self,
        path: str,
    ) -> list[str]:

        return [
            str(file)
            for file in Path(path).iterdir()
        ]

    def copy(
        self,
        source: str,
        destination: str,
    ) -> None:

        from shutil import copy2

        copy2(source, destination)

    def move(
        self,
        source: str,
        destination: str,
    ) -> None:

        Path(source).rename(destination)
