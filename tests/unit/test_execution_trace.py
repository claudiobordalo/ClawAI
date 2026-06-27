import pytest
from datetime import datetime, timezone
from clawai.tracing.execution_trace import ExecutionTraceManager, TraceEvent

def test_execution_trace_basic_flow():
    manager = ExecutionTraceManager()
    
    token = manager.start("TestComponent", "TestOperation")
    manager.finish(token, status="success", metadata={"key": "value"})
    
    events = manager.events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, TraceEvent)
    assert event.component == "TestComponent"
    assert event.operation == "TestOperation"
    assert event.status == "success"
    assert event.metadata == {"key": "value"}
    assert event.duration_ms >= 0
    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo == timezone.utc

def test_execution_trace_multiple_events():
    manager = ExecutionTraceManager()
    
    t1 = manager.start("C1", "O1")
    t2 = manager.start("C2", "O2")
    
    manager.finish(t1, status="success")
    manager.finish(t2, status="failure")
    
    events = manager.events()
    assert len(events) == 2
    assert events[0].operation == "O1"
    assert events[1].operation == "O2"
    assert events[1].status == "failure"

def test_execution_trace_duration_calculation():
    import time
    manager = ExecutionTraceManager()
    
    token = manager.start("Comp", "Op")
    time.sleep(0.05) # Sleep 50ms
    manager.finish(token)
    
    event = manager.events()[0]
    assert event.duration_ms >= 50

def test_execution_trace_missing_token():
    manager = ExecutionTraceManager()
    manager.finish("invalid-token")
    
    events = manager.events()
    assert len(events) == 1
    assert events[0].operation == "finish_missing_token"
    assert events[0].status == "error"

def test_execution_trace_clear():
    manager = ExecutionTraceManager()
    token = manager.start("C", "O")
    manager.finish(token)
    
    assert manager.size() == 1
    manager.clear()
    assert manager.size() == 0
    assert len(manager.events()) == 0

def test_execution_trace_empty_history():
    manager = ExecutionTraceManager()
    assert manager.size() == 0
    assert manager.events() == []

def test_execution_trace_immutability():
    # Test if TraceEvent is frozen
    from dataclasses import FrozenInstanceError
    event = TraceEvent(
        timestamp=datetime.now(timezone.utc),
        component="C",
        operation="O",
        status="S",
        duration_ms=1.0
    )
    with pytest.raises(FrozenInstanceError):
        event.status = "changed"

def test_execution_trace_concurrency():
    import threading
    manager = ExecutionTraceManager()
    
    def worker():
        for i in range(100):
            t = manager.start("ThreadComp", f"Op{i}")
            manager.finish(t)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert manager.size() == 1000

def test_execution_trace_chronological_order():
    manager = ExecutionTraceManager()
    
    t1 = manager.start("C1", "O1")
    manager.finish(t1)
    t2 = manager.start("C2", "O2")
    manager.finish(t2)
    
    events = manager.events()
    assert events[0].timestamp <= events[1].timestamp
