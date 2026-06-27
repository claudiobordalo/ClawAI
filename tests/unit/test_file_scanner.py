from __future__ import annotations

from pathlib import Path

from clawai.codebase import FileScanner


def test_file_scanner_empty_dir(tmp_path: Path) -> None:
    scanner = FileScanner()
    files = scanner.scan(tmp_path)
    assert files == ()


def test_file_scanner_multiple_files_and_order(tmp_path: Path) -> None:
    # Create structure
    (tmp_path / "a.py").write_text("print('a')")
    (tmp_path / "b.md").write_text("# b")
    (tmp_path / "z.json").write_text("{}")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("print('c')")

    scanner = FileScanner()
    files = scanner.scan(tmp_path)

    # Deterministic ordering (relative paths lexicographically)
    assert files == (
        "a.py",
        "b.md",
        "sub/c.py",
        "z.json",
    )


def test_file_scanner_extension_filter(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("print('a')")
    (tmp_path / "b.md").write_text("# b")
    (tmp_path / "c.txt").write_text("text")

    scanner = FileScanner()
    files = scanner.scan(tmp_path, exts=(".py",))
    assert files == ("a.py",)


def test_file_scanner_ignored_dirs(tmp_path: Path) -> None:
    ignored = [
        ".git",
        ".pytest_cache",
        "__pycache__",
        ".venv",
        ".env",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "node_modules",
    ]

    for d in ignored:
        p = tmp_path / d
        p.mkdir()
        (p / "ignore.py").write_text("print('x')")

    # Also add valid dir and file
    (tmp_path / "ok.py").write_text("print('ok')")

    scanner = FileScanner()
    files = scanner.scan(tmp_path)

    # Must contain only ok.py
    assert files == ("ok.py",)
