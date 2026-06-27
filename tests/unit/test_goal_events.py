from datetime import datetime, timezone

from clawai.goals import GoalEventBus, GoalEvent
from clawai.goals.goal_events import (
    GOAL_CREATED,
    GOAL_COMPLETED,
    GOAL_CANCELLED,
    GOAL_PROGRESS_UPDATED,
)


def test_event_creation():
    event = GoalEvent(
        timestamp=datetime.now(timezone.utc),
        event_type=GOAL_CREATED,
        goal_id="g1",
        metadata={"title": "Test"},
    )
    assert event.event_type == GOAL_CREATED
    assert event.goal_id == "g1"
    assert event.metadata["title"] == "Test"


def test_event_immutability():
    event = GoalEvent(
        timestamp=datetime.now(timezone.utc),
        event_type=GOAL_CREATED,
        goal_id="g1",
    )
    with pytest.raises(AttributeError):
        event.goal_id = "g2"  # type: ignore[misc]


import pytest


def test_event_bus_publish():
    bus = GoalEventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.subscribe(GOAL_CREATED, handler)
    event = GoalEvent(
        timestamp=datetime.now(timezone.utc),
        event_type=GOAL_CREATED,
        goal_id="g1",
    )
    bus.publish(event)
    assert len(received) == 1
    assert received[0].goal_id == "g1"


def test_event_bus_emit():
    bus = GoalEventBus()
    event = bus.emit(GOAL_CREATED, "g1", title="Test", priority=2)
    assert event.event_type == GOAL_CREATED
    assert event.goal_id == "g1"
    assert event.metadata["title"] == "Test"
    assert event.metadata["priority"] == 2


def test_event_bus_history():
    bus = GoalEventBus()
    bus.emit(GOAL_CREATED, "g1")
    bus.emit(GOAL_COMPLETED, "g1")
    bus.emit(GOAL_CANCELLED, "g1")
    history = bus.history()
    assert len(history) == 3
    assert history[0].event_type == GOAL_CREATED
    assert history[1].event_type == GOAL_COMPLETED
    assert history[2].event_type == GOAL_CANCELLED


def test_event_bus_clear():
    bus = GoalEventBus()
    bus.emit(GOAL_CREATED, "g1")
    bus.clear()
    assert bus.history() == tuple()


def test_event_bus_multiple_subscribers():
    bus = GoalEventBus()
    results = []

    def h1(e):
        results.append("h1")

    def h2(e):
        results.append("h2")

    bus.subscribe(GOAL_CREATED, h1)
    bus.subscribe(GOAL_CREATED, h2)
    bus.emit(GOAL_CREATED, "g1")
    assert len(results) == 2


def test_event_bus_different_types():
    bus = GoalEventBus()
    created = []
    completed = []

    bus.subscribe(GOAL_CREATED, lambda e: created.append(e))
    bus.subscribe(GOAL_COMPLETED, lambda e: completed.append(e))

    bus.emit(GOAL_CREATED, "g1")
    bus.emit(GOAL_COMPLETED, "g1")
    bus.emit(GOAL_CANCELLED, "g2")

    assert len(created) == 1
    assert len(completed) == 1


def test_event_constants():
    assert GOAL_CREATED == "goal.created"
    assert GOAL_COMPLETED == "goal.completed"
    assert GOAL_CANCELLED == "goal.cancelled"
    assert GOAL_PROGRESS_UPDATED == "goal.progress_updated"


def test_event_default_metadata():
    event = GoalEvent(
        timestamp=datetime.now(timezone.utc),
        event_type=GOAL_CREATED,
        goal_id="g1",
    )
    assert event.metadata == {}
