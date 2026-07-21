from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class MissionCost(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class ResourceLimits:
    cpu_busy_percent: float = 85.0
    ram_busy_percent: float = 85.0
    disk_busy_percent: float = 95.0
    critical_processes: tuple[str, ...] = (
        "gta5.exe",
        "dofus.exe",
        "ankama launcher.exe",
        "blender.exe",
        "unrealeditor.exe",
        "unity.exe",
        "cl.exe",
        "msbuild.exe",
        "ninja.exe",
    )


@dataclass(slots=True)
class ResourceSnapshot:
    cpu_percent: float | None
    ram_percent: float | None
    disk_percent: float | None
    gpu_percent: float | None = None
    vram_percent: float | None = None
    temperature_celsius: float | None = None
    active_processes: tuple[str, ...] = ()


@dataclass(slots=True)
class AdaptationDecision:
    action: str
    reason: str
    mission_cost: MissionCost
    max_threads: int
    model_size: str
    prefer_cpu: bool
    should_pause: bool
    critical_processes: tuple[str, ...]


class ResourceProbe(Protocol):

    def snapshot(self) -> ResourceSnapshot:
        pass


class SystemResourceProbe:
    """
    Coleta informacoes basicas sem dependencias externas.
    """

    def snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(
            cpu_percent=None,
            ram_percent=None,
            disk_percent=self._disk_percent(),
            active_processes=self._active_processes(),
        )

    def _disk_percent(self) -> float | None:
        try:
            usage = shutil.disk_usage(os.getcwd())
        except OSError:
            return None

        if usage.total == 0:
            return None

        return (usage.used / usage.total) * 100

    def _active_processes(self) -> tuple[str, ...]:
        system = platform.system().lower()

        if system == "windows":
            command = ["tasklist", "/fo", "csv", "/nh"]
        else:
            command = ["ps", "-eo", "comm="]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
                timeout=3,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ()

        if result.returncode != 0:
            return ()

        return tuple(self._parse_process_lines(result.stdout.splitlines()))

    def _parse_process_lines(
        self,
        lines: list[str],
    ) -> list[str]:
        names: list[str] = []

        for line in lines:
            value = line.strip()

            if not value:
                continue

            if value.startswith('"'):
                value = value.split('","', 1)[0].strip('"')
            else:
                value = value.split()[0]

            names.append(value.lower())

        return names


class ResourceManager:

    def __init__(
        self,
        limits: ResourceLimits | None = None,
        probe: ResourceProbe | None = None,
    ) -> None:
        self._limits = limits or ResourceLimits()
        self._probe = probe or SystemResourceProbe()

    def snapshot(self) -> ResourceSnapshot:
        return self._probe.snapshot()

    def estimate_mission_cost(
        self,
        objective: str,
        expected_files: int = 0,
    ) -> MissionCost:
        length = len(objective)

        if length > 4000 or expected_files > 25:
            return MissionCost.HIGH

        if length > 1000 or expected_files > 8:
            return MissionCost.MEDIUM

        return MissionCost.LOW

    def decide(
        self,
        objective: str,
        expected_files: int = 0,
    ) -> AdaptationDecision:
        snapshot = self.snapshot()
        cost = self.estimate_mission_cost(
            objective=objective,
            expected_files=expected_files,
        )
        critical = self._critical_processes(snapshot)
        busy_reasons = self._busy_reasons(snapshot)

        if critical and cost is MissionCost.HIGH:
            return AdaptationDecision(
                action="defer",
                reason="critical_process_active",
                mission_cost=cost,
                max_threads=1,
                model_size="small",
                prefer_cpu=True,
                should_pause=True,
                critical_processes=critical,
            )

        if critical or busy_reasons:
            reason_parts = list(busy_reasons)

            if critical:
                reason_parts.append("critical_process_active")

            return AdaptationDecision(
                action="reduce",
                reason=",".join(reason_parts),
                mission_cost=cost,
                max_threads=1,
                model_size="small",
                prefer_cpu=True,
                should_pause=False,
                critical_processes=critical,
            )

        return AdaptationDecision(
            action="continue",
            reason="resources_available",
            mission_cost=cost,
            max_threads=max(1, min(4, os.cpu_count() or 1)),
            model_size="normal",
            prefer_cpu=False,
            should_pause=False,
            critical_processes=(),
        )

    def _critical_processes(
        self,
        snapshot: ResourceSnapshot,
    ) -> tuple[str, ...]:
        active = {name.lower() for name in snapshot.active_processes}

        return tuple(
            name
            for name in self._limits.critical_processes
            if name.lower() in active
        )

    def _busy_reasons(
        self,
        snapshot: ResourceSnapshot,
    ) -> tuple[str, ...]:
        reasons: list[str] = []

        if self._exceeds(snapshot.cpu_percent, self._limits.cpu_busy_percent):
            reasons.append("cpu_busy")

        if self._exceeds(snapshot.ram_percent, self._limits.ram_busy_percent):
            reasons.append("ram_busy")

        if self._exceeds(snapshot.disk_percent, self._limits.disk_busy_percent):
            reasons.append("disk_busy")

        return tuple(reasons)

    def _exceeds(
        self,
        value: float | None,
        limit: float,
    ) -> bool:
        return value is not None and value >= limit
