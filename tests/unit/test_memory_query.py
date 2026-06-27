from clawai.engineering import MemoryQuery


def test_memory_query_defaults_and_overrides():
    q = MemoryQuery()
    assert q.objective is None and q.target_query is None and q.diagnosis is None and q.success_only is None

    q2 = MemoryQuery(objective="A", target_query="B", diagnosis="C", success_only=True)
    assert q2.objective == "A" and q2.target_query == "B" and q2.diagnosis == "C" and q2.success_only is True

    q3 = MemoryQuery(success_only=False)
    assert q3.success_only is False
