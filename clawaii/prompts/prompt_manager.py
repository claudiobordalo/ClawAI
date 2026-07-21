from pathlib import Path


class PromptManager:

    def __init__(
        self,
        root: Path | str = "configs/prompts",
    ) -> None:
        self._root = Path(root)

    def load(
        self,
        name: str,
    ) -> str:

        return (
            self._root / f"{name}.md"
        ).read_text(
            encoding="utf-8",
        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return (
            self._root / f"{name}.md"
        ).exists()

    def list(
        self,
    ) -> list[str]:

        return sorted(
            file.stem
            for file in self._root.glob("*.md")
        )

