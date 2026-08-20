from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .models import GitOperationResult, GitSnapshot

ROOT = Path(__file__).resolve().parents[2]


class GitService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT
        self._git = shutil.which("git") or "git"

    def available(self) -> bool:
        return shutil.which("git") is not None

    def _run(self, *args: str) -> GitOperationResult:
        command = [self._git, *args]

        if not self.available():
            return GitOperationResult(
                success=False,
                return_code=127,
                stdout="",
                stderr="git executable not found",
                command=" ".join(command),
            )

        completed = subprocess.run(
            command,
            cwd=str(self.root),
            capture_output=True,
            text=True,
            shell=False,
        )

        return GitOperationResult(
            success=completed.returncode == 0,
            return_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            command=" ".join(command),
        )

    def current_branch(self) -> GitOperationResult:
        return self._run("branch", "--show-current")

    def current_commit(self) -> GitOperationResult:
        return self._run("rev-parse", "HEAD")

    def status_porcelain(self) -> GitOperationResult:
        return self._run("status", "--porcelain")

    def capture_snapshot(self) -> GitSnapshot:
        branch_result = self.current_branch()
        branch = branch_result.stdout.strip()
        if not branch:
            fallback = self._run("rev-parse", "--abbrev-ref", "HEAD")
            branch = fallback.stdout.strip() or "main"
            if branch == "HEAD":
                branch = "main"

        commit_result = self.current_commit()
        commit = commit_result.stdout.strip()
        dirty = bool(self.status_porcelain().stdout.strip())
        return GitSnapshot(branch=branch, commit=commit, dirty=dirty)

    def create_branch(self, branch_name: str, start_point: str | None = None) -> GitOperationResult:
        if start_point:
            return self._run("checkout", "-B", branch_name, start_point)
        return self._run("checkout", "-B", branch_name)

    def checkout(self, branch_name: str) -> GitOperationResult:
        return self._run("checkout", branch_name)

    def reset_hard(self, ref: str) -> GitOperationResult:
        return self._run("reset", "--hard", ref)

    def add_all(self) -> GitOperationResult:
        return self._run("add", "-A")

    def commit(self, message: str) -> GitOperationResult:
        return self._run("commit", "--allow-empty", "-m", message)

    def merge_ff_only(self, target_branch: str, source_branch: str) -> GitOperationResult:
        current = self.current_branch().stdout.strip()
        checkout_result = self.checkout(target_branch)
        if not checkout_result.success:
            return checkout_result

        merge_result = self._run("merge", "--ff-only", source_branch)
        if current and current != target_branch:
            self.checkout(current)
        return merge_result
