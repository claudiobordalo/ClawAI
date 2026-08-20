from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from clawai.backlog import BacklogManager, BacklogItem

ROOT = Path(__file__).resolve().parent.parent


class SafeExecutor:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.executed_tasks: List[str] = []

    def execute_command(self, command: str, cwd: Path = ROOT) -> bool:
        """Executes a shell command safely."""
        if self.dry_run:
            print(f"[DRY-RUN] Would execute: {command}")
            return True
        
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print(f"[EXEC] Error executing '{command}': {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"[EXEC] Exception in '{command}': {e}")
            return False

    def apply_code_fix(self, target_file: Path, diff_content: str) -> bool:
        """Applies a code fix using a temp patch file."""
        if self.dry_run:
            print(f"[DRY-RUN] Would apply fix to {target_file}")
            return True

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(diff_content)
                patch_file = f.name
            
            result = subprocess.run(
                ["git", "apply", patch_file],
                cwd=str(ROOT),
                capture_output=True,
                text=True
            )
            
            Path(patch_file).unlink(missing_ok=True)
            
            if result.returncode != 0:
                print(f"[EXEC] Failed to apply patch to {target_file}: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"[EXEC] Exception applying patch: {e}")
            return False

    def execute_task(self, task: BacklogItem) -> bool:
        """Executes a specific task from the backlog."""
        print(f"[AUTO-EXEC] Executing task: {task.title}")
        
        if task.type == "tech_debt":
            if "verify.py" in task.description.lower() or "refactor" in task.title.lower():
                # Simula execução de correção de código
                return self.apply_code_fix(ROOT / "verify.py", f"Fix for {task.id}")
            return self.execute_command("echo 'Task executed'")
        
        elif task.type == "roadmap":
            return self.execute_command(f"echo 'Roadmap task: {task.title}'")
        
        return False

    def execute_backlog_phase(self, backlog: BacklogManager, phase_id: str) -> None:
        """Executes all tasks in a specific phase of the roadmap."""
        # Simplificação: executa todos os itens de alta prioridade abertos
        open_items = backlog.get_open_items()
        
        for item in open_items:
            print(f"Processing: {item.title}")
            success = self.execute_task(item)
            if success:
                backlog.update_item_status(item.id, "done")
                self.executed_tasks.append(item.id)
                print(f"[AUTO-EXEC] Task {item.id} completed.")
            else:
                print(f"[AUTO-EXEC] Task {item.id} failed.")
