from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

from .backlog import BacklogManager

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "verify_report.json"

DEBT_KEYWORDS = ["TODO", "FIXME", "HACK", "XXX"]


def scan_codebase_for_debt() -> List[Tuple[str, int, str]]:
    """Scans the codebase for debt keywords (TODO, FIXME, etc.)."""
    findings = []
    paths_to_scan = [ROOT / "api.py"] + list((ROOT / "clawai").rglob("*.py"))

    for file_path in paths_to_scan:
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                for keyword in DEBT_KEYWORDS:
                    if keyword in line:
                        comment = line.split(keyword)[1].strip().strip(":").strip()
                        if comment:
                            findings.append((str(file_path.relative_to(ROOT)), i, f"{keyword}: {comment}"))
        except Exception:
            pass
    return findings


def check_verify_report() -> str | None:
    """Checks the latest verify report for issues."""
    if not REPORT_PATH.exists():
        return None
    try:
        data = json.loads(REPORT_PATH.read_text())
        if data.get("status") == "FAIL":
            return "FAIL"
        if data.get("warnings", 0) > 0:
            return f"{data['warnings']} warnings found"
        return None
    except Exception:
        return None


def run_auto_diagnosis(backlog: BacklogManager) -> None:
    """Runs diagnosis and updates the backlog."""
    # 1. Check codebase
    findings = scan_codebase_for_debt()
    seen_titles = set()
    
    for file, line, desc in findings:
        title = f"Code Issue in {file}:{line}"
        if title not in seen_titles:
            backlog.add_item(
                type="tech_debt",
                title=title,
                description=desc,
                priority=3,
                tags=["auto-diagnosis"]
            )
            seen_titles.add(title)

    # 2. Check verify report
    report_status = check_verify_report()
    if report_status:
        backlog.add_item(
            type="tech_debt",
            title="Verification Issue Detected",
            description=f"Last verify report status: {report_status}",
            priority=2,
            tags=["auto-diagnosis"]
        )
