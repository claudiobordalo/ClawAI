from dataclasses import dataclass, field
from contextlib import contextmanager
from typing import Iterator, Any
import time

@dataclass
class RuntimeProfile:

    name: str
    elapsed_ms: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class RuntimeProfiler:

    def __init__(self):
        self.entries = []

    @contextmanager
    def measure(self, name, metadata=None) -> Iterator[RuntimeProfile]:

        profile = RuntimeProfile(name=name,
                                 metadata=metadata or {})

        start = time.perf_counter()

        try:
            yield profile

        finally:

            profile.elapsed_ms = \
                (time.perf_counter()-start)*1000

            self.entries.append(profile)

    def snapshot(self):

        return {
            "entries":[
                {
                    "name":e.name,
                    "elapsed_ms":e.elapsed_ms,
                    "metadata":e.metadata
                }
                for e in self.entries
            ]
        }