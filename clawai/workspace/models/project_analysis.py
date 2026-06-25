from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProjectAnalysis:

    languages: set[str] = field(default_factory=set)
    frameworks: set[str] = field(default_factory=set)
    package_managers: set[str] = field(default_factory=set)
    tools: set[str] = field(default_factory=set)
    ci_cd: set[str] = field(default_factory=set)
