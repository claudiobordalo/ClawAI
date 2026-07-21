from __future__ import annotations

from datetime import datetime
from pathlib import Path


class KnowledgeBase:

    def __init__(
        self,
        root: str | Path = ".clawai/knowledge"
    ) -> None:

        self.root = Path(root)

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def topics(self) -> list[str]:

        return sorted(
            file.stem
            for file in self.root.glob("*.md")
        )

    def read(
        self,
        topic: str,
    ) -> str:

        file = self.root / f"{topic}.md"

        if not file.exists():
            return ""

        return file.read_text(
            encoding="utf-8"
        )

    def append(
        self,
        topic: str,
        title: str,
        content: str,
    ) -> None:

        file = self.root / f"{topic}.md"

        with file.open(
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                f"""

## {title}

_Data:_ {datetime.utcnow().isoformat()}

{content}

---
"""
            )

    def search(
        self,
        query: str,
    ) -> list[dict]:

        words = {
            word.lower()
            for word in query.split()
            if len(word) > 2
        }

        results = []

        for file in self.root.glob("*.md"):

            text = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            lower = text.lower()

            score = sum(
                word in lower
                for word in words
            )

            if score:

                results.append(
                    {
                        "topic": file.stem,
                        "score": score,
                        "content": text,
                    }
                )

        results.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return results


knowledge = KnowledgeBase()
