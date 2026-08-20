from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Episode:

    timestamp: str

    objective: str

    plan: str

    outcome: str

    success: bool

    notes: str = ""


class EpisodicMemory:

    def __init__(self) -> None:

        self.file = Path(".clawai/episodic_memory.json")

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file.exists():

            self.file.write_text(
                "[]",
                encoding="utf-8",
            )

    def save(
        self,
        episode: Episode,
    ) -> None:

        data = self.load()

        data.append(
            asdict(episode)
        )

        self.file.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def load(self):

        return json.loads(

            self.file.read_text(
                encoding="utf-8",
            )

        )

    def search(
        self,
        text: str,
    ):

        text = text.lower()

        result = []

        for item in self.load():

            if (
                text in item["objective"].lower()
                or
                text in item["plan"].lower()
                or
                text in item["notes"].lower()
            ):

                result.append(item)

        return result


episodic_memory = EpisodicMemory()
