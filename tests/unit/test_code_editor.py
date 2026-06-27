from __future__ import annotations

from clawai.editor import CodeEditor, EditOperation


def test_code_editor_apply_success(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("A", encoding="utf-8")

    editor = CodeEditor()
    op = EditOperation(file=f, original_content="A", new_content="B", reason="step1")

    res = editor.apply(op)
    assert res.success is True
    assert f.read_text(encoding="utf-8") == "B"


def test_code_editor_apply_validation_failure(tmp_path):
    f = tmp_path / "b.txt"
    f.write_text("X", encoding="utf-8")

    editor = CodeEditor()
    # Wrong original content triggers validator failure; file should not change
    op = EditOperation(file=f, original_content="WRONG", new_content="Y", reason="bad")

    res = editor.apply(op)
    assert res.success is False
    assert f.read_text(encoding="utf-8") == "X"


def test_code_editor_apply_many_interrupts_on_first_failure(tmp_path):
    f = tmp_path / "c.txt"
    f.write_text("0", encoding="utf-8")

    editor = CodeEditor()

    ops = [
        EditOperation(file=f, original_content="0", new_content="1", reason="to1"),
        EditOperation(file=f, original_content="WRONG", new_content="2", reason="bad"),
        EditOperation(file=f, original_content="1", new_content="3", reason="to3"),  # should not run
    ]

    results = editor.apply_many(ops)

    assert len(results) == 2  # interrupted after first failure
    assert results[0].success is True
    assert results[1].success is False
    assert f.read_text(encoding="utf-8") == "1"  # only first applied


def test_code_editor_apply_many_order_and_determinism(tmp_path):
    f1 = tmp_path / "d1.txt"
    f1.write_text("a", encoding="utf-8")

    f2 = tmp_path / "d2.txt"
    f2.write_text("x", encoding="utf-8")

    editor = CodeEditor()

    ops = [
        EditOperation(file=f1, original_content="a", new_content="b", reason="r1"),
        EditOperation(file=f2, original_content="x", new_content="y", reason="r2"),
    ]

    r1 = editor.apply_many(ops)

    # Reset files to initial state to assert determinism across identical runs
    f1.write_text("a", encoding="utf-8")
    f2.write_text("x", encoding="utf-8")

    r2 = editor.apply_many(ops)

    assert r1 == r2
    assert f1.read_text(encoding="utf-8") == "b"
    assert f2.read_text(encoding="utf-8") == "y"


def test_code_editor_full_integration(tmp_path):
    f = tmp_path / "e.txt"
    f.write_text("start", encoding="utf-8")

    editor = CodeEditor()

    ops = [
        EditOperation(file=f, original_content="start", new_content="mid", reason="step1"),
        EditOperation(file=f, original_content="mid", new_content="end", reason="step2"),
    ]

    results = editor.apply_many(ops)

    assert all(r.success for r in results)
    assert f.read_text(encoding="utf-8") == "end"
