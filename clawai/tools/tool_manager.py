from __future__ import annotations

from pathlib import Path


class ToolManager:

    def __init__(
        self,
        root: str | Path,
    ) -> None:

        self.root = Path(root)

    def read_file(
        self,
        path: str,
    ) -> str:

        return (
            self.root / path
        ).read_text(
            encoding="utf-8",
            errors="ignore",
        )

    def write_file(
        self,
        path: str,
        content: str,
    ) -> None:

        target = self.root / path

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

    def list_directory(
        self,
        path: str = ".",
    ) -> list[str]:

        root = self.root / path

        return sorted(

            str(
                p.relative_to(self.root)
            ).replace("\\", "/")

            for p in root.rglob("*")

        )

    def search_project(
        self,
        text: str,
    ) -> list[str]:

        result = []

        for file in self.root.rglob("*"):

            if not file.is_file():
                continue

            try:

                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

            except Exception:
                continue

            if text.lower() in content.lower():

                result.append(
                    str(
                        file.relative_to(
                            self.root
                        )
                    ).replace("\\", "/")
                )

        return sorted(result)


tools = ToolManager(".")
