from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class Memory:

    def __init__(
        self,
        root: str | Path = ".clawai/memory"
    ) -> None:

        self.root = Path(root)
        self.root.mkdir(
            parents=True,
            exist_ok=True
        )

    def _file(
        self,
        category: str,
    ) -> Path:

        return self.root / f"{category}.json"

    def load(
        self,
        category: str,
    ) -> list[dict]:

        file = self._file(category)

        if not file.exists():
            return []

        return json.loads(
            file.read_text(
                encoding="utf-8"
            )
        )

    def add(
        self,
        category: str,
        title: str,
        content: str,
        source: str = "user"
    ) -> None:

        data = self.load(category)

        data.append(
            {
                "title": title,
                "content": content,
                "source": source,
                "created_at": datetime.utcnow().isoformat()
            }
        )

        self._file(category).write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    def search(
        self,
        category: str,
        query: str,
        limit: int = 10
    ) -> list[dict]:

        query = query.lower()

        results = []

        for item in self.load(category):

            score = 0

            text = (
                item["title"] +
                " " +
                item["content"]
            ).lower()

            for word in query.split():

                if word in text:
                    score += 1

            if score:

                item = dict(item)
                item["score"] = score
                results.append(item)

        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return results[:limit]


memory = Memory()
