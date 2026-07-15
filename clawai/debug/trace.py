from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
import json
from pathlib import Path


@dataclass
class TraceEvent:

    stage: str
    timestamp: str
    data: object


class RuntimeTrace:

    def __init__(self):

        self.id = uuid.uuid4().hex[:10]

        self.events = []

    def add(self, stage, data):

        self.events.append(

            TraceEvent(
                stage,
                datetime.now(timezone.utc).isoformat(),
                data
            )
        )

    def save(self):

        folder = Path(".clawai/traces")

        folder.mkdir(parents=True,
                     exist_ok=True)

        file = folder / f"{self.id}.json"

        file.write_text(

            json.dumps(
                self.snapshot(),
                indent=2,
                ensure_ascii=False,
                default=str
            ),

            encoding="utf8"
        )

    def snapshot(self):

        return {

            "id":self.id,

            "events":[
                e.__dict__
                for e in self.events
            ]
        }