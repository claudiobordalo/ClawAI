from clawai.resources import MissionCost
from clawai.resources import ResourceLimits
from clawai.resources import ResourceManager
from clawai.resources import ResourceSnapshot


class FakeProbe:

    def __init__(
        self,
        snapshot: ResourceSnapshot,
    ) -> None:
        self._snapshot = snapshot

    def snapshot(self) -> ResourceSnapshot:
        return self._snapshot


def test_resource_manager_continues_when_resources_are_available() -> None:

    manager = ResourceManager(
        probe=FakeProbe(
            ResourceSnapshot(
                cpu_percent=20,
                ram_percent=30,
                disk_percent=40,
                active_processes=(),
            )
        )
    )

    decision = manager.decide("small task")

    assert decision.action == "continue"
    assert decision.should_pause is False
    assert decision.model_size == "normal"


def test_resource_manager_reduces_when_critical_process_is_active() -> None:

    manager = ResourceManager(
        limits=ResourceLimits(critical_processes=("dofus.exe",)),
        probe=FakeProbe(
            ResourceSnapshot(
                cpu_percent=20,
                ram_percent=30,
                disk_percent=40,
                active_processes=("dofus.exe",),
            )
        ),
    )

    decision = manager.decide("small task")

    assert decision.action == "reduce"
    assert decision.prefer_cpu is True
    assert decision.max_threads == 1
    assert decision.critical_processes == ("dofus.exe",)


def test_resource_manager_defers_high_cost_mission_when_critical_process_is_active() -> None:

    manager = ResourceManager(
        limits=ResourceLimits(critical_processes=("gta5.exe",)),
        probe=FakeProbe(
            ResourceSnapshot(
                cpu_percent=20,
                ram_percent=30,
                disk_percent=40,
                active_processes=("gta5.exe",),
            )
        ),
    )

    decision = manager.decide(
        "large task",
        expected_files=40,
    )

    assert decision.action == "defer"
    assert decision.should_pause is True
    assert decision.mission_cost is MissionCost.HIGH


def test_resource_manager_reduces_when_resources_are_busy() -> None:

    manager = ResourceManager(
        probe=FakeProbe(
            ResourceSnapshot(
                cpu_percent=90,
                ram_percent=30,
                disk_percent=40,
                active_processes=(),
            )
        )
    )

    decision = manager.decide("small task")

    assert decision.action == "reduce"
    assert decision.reason == "cpu_busy"
