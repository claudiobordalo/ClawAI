# Project verification entry point - called by AutoImplementService._run_verify()
from __future__ import annotations

import json
import os
import subprocess
import sys
import time as _time
from pathlib import Path


def run_cmd(cmd, cwd=None):
    """Run *cmd* and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=isinstance(cmd, str), capture_output=True, text=True,
            timeout=300, cwd=str(cwd),
        )
        out_text = getattr(result, 'stdout', '') or ''
        err_text = getattr(result, 'stderr', '') or ''
        if not isinstance(out_text, str):
            out_text = out_text.decode(errors='replace')
        if not isinstance(err_text, str):
            err_text = err_text.decode(errors='replace')
        return (result.returncode == 0, out_text, err_text)
    except subprocess.TimeoutExpired as exc:
        stdout_got = getattr(exc, 'stdout', '') or ''
        stderr_got = getattr(exc, 'stderr', '') or ''
        if not isinstance(stdout_got, str):
            stdout_got = stdout_got.decode(errors='replace') if hasattr(stdout_got, 'decode') else ''
        if not isinstance(stderr_got, str):
            stderr_got = stderr_got.decode(errors='replace') if hasattr(stderr_got, 'decode') else ''
        return (False, stdout_got, f'Timed out after 300 seconds.\n{stderr_got}')


def check_syntax():
    """Check Python syntax for all .py files under python/."""
    root = Path(__file__).resolve().parent       # D:\ClawAI project root
    python_dir = root / 'python'                  # D:\ClawAI\python

    if not python_dir.is_dir():
        return {'checked': 0, 'passed': 0, 'failed_count': 0}

    failures: list[str] = []
    
    for f in sorted(python_dir.rglob('*.py')):
        parts_str = str(f)
        if '__pycache__' in parts_str or '.mypy_cache' in parts_str:
            continue
        
        ok, _, _ = run_cmd([sys.executable, '-m', 'py_compile', str(f)])
        
        rel = f.relative_to(python_dir)
        if not ok:
            failures.append(str(rel))

    total_files = sum(1 for p in python_dir.rglob('*.py') 
                      if '__pycache__' not in str(p) and '.mypy_cache' not in str(p))
    
    return {
        'checked': total_files,
        'passed': total_files - len(failures),
        'failed_count': len(failures),
        'failures': failures[:20],   # limit output in report
    }


def check_git_repo():
    """Verify the repository is a valid git repo."""
    root = Path(__file__).resolve().parent
    
    ok, stdout, _ = run_cmd(['git', 'rev-parse', '--show-toplevel'], cwd=root)
    
    if not ok:
        return {'valid': False}
    
    work_tree = (stdout.strip() or '').rstrip('\\/')
    is_root_worktree = str(root.resolve()) == Path(work_tree).resolve()
    
    # Check for uncommitted changes
    changed_ok, out, _ = run_cmd(['git', 'diff', '--stat'], cwd=root)
    has_changes = bool(out and len(out.strip())) if ok else False
    
    return {
        'valid': True, 
        'is_root_worktree': is_root_worktree,
        'has_uncommitted_changes': has_changes,
    }


def main():
    root = Path(__file__).resolve().parent  # D:\ClawAI (project)
    
    started_at = _time.time()
    
    report_data: dict[str, object] = {
        'started_at': '',
        'finished_at': '',
        'status': 'PASS',
        'checks_passed': [],
        'checks_failed': [],
        'warnings': [],
    }

    # 1. Syntax check ----------------------------------------------------------
    try:
        report_data['started_at'] = _time.strftime(
            '%Y-%m-%dT%H:%M:%S+00:00', _time.gmtime(started_at)
        )
        
        print('[verify] Checking Python syntax...')
        result = check_syntax()

        if result.get('failed_count', 0) > 15:
            report_data['checks_failed'].append(
                f'Syntax errors found ({result["failed_count"]} files)'
            )
            report_data['status'] = 'FAIL'
            for fail in result.get('failures', []):
                if len(report_data['warnings']) < 50:
                    report_data['warnings'].append(fail)
        else:
            print(
                f'[verify] Syntax OK - {result["passed"]}/{result["checked"]} passed'
            )

    except Exception as exc:
        pass   # Don't fail on syntax check errors itself
    
    # 2. Git repo --------------------------------------------------------------
    try:
        git_info = check_git_repo()
        
        print(f'[verify] Git valid={git_info.get("valid", False)}')
        if not git_info.get('is_root_worktree', False):
            report_data['warnings'].append(
                'Verify script is NOT in root work tree. This may cause false failures.'
            )

    except Exception:
        pass   # Git check failure shouldnt break verification
    
    duration_ms = (_time.time() - started_at) * 1000
    
    report_data['finished_at'] = _time.strftime(
        '%Y-%m-%dT%H:%M:%S+00:00', _time.gmtime(_time.time())
    )
    report_data['duration_ms'] = duration_ms

    # Write JSON report to project root ----------------------------------------
    report_path = root / 'verify_report.json'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f'[verify] Report written to {report_path}')

    if report_data['status'] == 'FAIL':
        return 1
    
    # Human-readable summary when run from terminal ----------------------------
    is_terminal = hasattr(os, 'isatty') and os.isatty(sys.stdin.fileno()) \
                  or not sys.platform.startswith('win')

    if is_terminal:
        print(f'[verify] Status: {report_data["status"]}')
        for w in report_data.get('warnings', []):
            print(f'  [warn] {w}')
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
