from datetime import datetime, timezone

from clawai.engineering import EngineeringMemory, EngineeringRecord, MemoryQuery


def _rec(obj: str, diag: str, success: bool, mods: tuple[str, ...] = tuple()) -> EngineeringRecord:
    return EngineeringRecord(
        timestamp=datetime.now(timezone.utc),
        objective=obj,
        target_query="core",
        instructions="instr",
        diagnosis=diag,
        strategy="RepairStrategy",
        summary="sum",
        success=success,
        modified_files=mods,
        failed_tests=("t::a",) if not success else tuple(),
        duration=0.5,
    )


def test_memory_add_clear_size_last_and_determinism():
    mem = EngineeringMemory()
    assert mem.size() == 0

    r1 = _rec("O1", "D1", True)
    r2 = _rec("O2", "D2", False)
    r3 = _rec("O3", "D1", True)

    mem.add(r1)
    mem.add(r2)
    mem.add(r3)

    assert mem.size() == 3
    assert mem.last(0) == tuple()
    assert mem.last(2) == (r2, r3)

    # Deterministic query order equals insertion order
    q_all = mem.query(MemoryQuery())
    assert q_all.records == (r1, r2, r3)

    # Clear
    mem.clear()
    assert mem.size() == 0


def test_memory_query_filters_and_and_semantics():
    mem = EngineeringMemory()
    r1 = _rec("O", "D1", True, mods=("a.py",))
    r2 = _rec("O", "D2", False, mods=("b.py",))
    r3 = _rec("P", "D1", True, mods=("c.py",))
    for r in (r1, r2, r3):
        mem.add(r)

    # objective
    q_obj = mem.query(MemoryQuery(objective="O"))
    assert q_obj.records == (r1, r2)

    # diagnosis
    q_diag = mem.query(MemoryQuery(diagnosis="D1"))
    assert q_diag.records == (r1, r3)

    # success_only
    q_succ = mem.query(MemoryQuery(success_only=True))
    assert q_succ.records == (r1, r3)

    # multiple filters (AND)
    q_multi = mem.query(MemoryQuery(objective="O", diagnosis="D1", success_only=True))
    assert q_multi.records == (r1,)
