from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Prompt:

    name: str
    content: str
