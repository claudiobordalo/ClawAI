import os
import json
import ast
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from collections import Counter

@dataclass
class EvolutionTask:
    id: str
    title: str
    description: str
    priority: int  # 1 (Low) to 5 (Critical)
    category: str  # e.g., "Refactoring", "Modernization", "Performance", "Security"
    status: str  # "backlog", "planned", "in_progress", "completed"
    impact_score: float
    requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "status": self.status,
            "impact_score": self.impact_score,
            "requirements": self.requirements,
            "metadata": self.metadata
        }

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

class BatchAuditor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.backlog_path = self.project_root / "growth_backlog.json"
        self.import_counts = Counter()

    def audit_directory(self, target_dir: str, chunk_size: int = 50):
        target_path = Path(target_dir).resolve()
        print(f"🔍 Auditing directory: {target_path}")
        
        # Get all python files in the target directory (recursive)
        py_files = [p for p in target_path.rglob("*.py") 
                     if not any(part in p.parts for part in ["__pycache__", ".git", "node_modules", "dist"])]
        
        print(f"📂 Found {len(py_files)} files to analyze.")

        tasks = []
        # Process in chunks to avoid timeouts and memory issues
        for i in range(0, len(py_files), chunk_size):
            chunk = py_files[i : i + chunk_size]
            print(f"📦 Processing chunk {i // chunk_size + 1} ({len(chunk)} files)...")
            
            for path in chunk:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                    
                    relative_path = str(path.relative_to(self.project_root))
                    size = path.stat().st_size

                    # 1. Size check
                    if size > 20000:
                        tasks.append(EvolutionTask(
                            id=f"EVO-{len(tasks)+1}",
                            title=f"Refactor {path.name}",
                            description=f"Large file ({size} bytes).",
                            priority=3, category="Refactoring", status="backlog", impact_score=0.6,
                            requirements=[relative_path]
                        ))

                    # 2. AST Analysis for Type Hints and Complexity
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            has_hints = bool(node.returns) or any(hasattr(arg, 'annotation') for arg in node.args.args)
                            if not has_hints:
                                tasks.append(EvolutionTask(
                                    id=f"EVO-{len(tasks)+1}",
                                    title=f"Type Hints in {path.name}",
                                    description=f"Function '{node.name}' missing annotations.",
                                    priority=2, category="Modernization", status="backlog", impact_score=0.4,
                                    requirements=[relative_path, f"Function: {node.name}"]
                                ))
                            
                            visitor = ComplexityVisitor()
                            visitor.visit(node)
                            if visitor.complexity > 15:
                                tasks.append(EvolutionTask(
                                    id=f"EVO-{len(tasks)+1}",
                                    title=f"Simplify {node.name} (Comp: {visitor.complexity})",
                                    description=f"High complexity in {path.name}.",
                                    priority=4, category="Refactoring", status="backlog", impact_score=0.9,
                                    requirements=[relative_path, f"Function: {node.name}"]
                                ))

                    # 3. Dependency Check (Simplified)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self.import_counts[relative_path] += 1
                        elif isinstance(node, ast.ImportFrom):
                            self.import_counts[relative_path] += 1

                    if self.import_counts[relative_path] > 5:
                        tasks.append(EvolutionTask(
                            id=f"EVO-{len(tasks)+1}",
                            title=f"Critical Dependency: {path.name}",
                            description=f"High number of imports ({self.import_counts[relative_path]}).",
                            priority=5, category="Architecture", status="backlog", impact_score=1.0,
                            requirements=[relative_path]
                        ))

                except Exception as e:
                    print(f"⚠️ Skipping {path} due to error: {e}")
            
            # Save progress after each chunk
            self.save_tasks(tasks)

        print(f"✅ Audit complete. Total tasks identified: {len(tasks)}")

    def save_tasks(self, new_tasks: List[EvolutionTask]):
        existing_tasks = []
        if self.backlog_path.exists():
            try:
                with open(self.backlog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing_tasks = [EvolutionTask(**item) for item in data]
            except Exception: pass

        existing_ids = {t.id for t in existing_tasks}
        for task in new_tasks:
            if task.id not in existing_ids:
                existing_tasks.append(task)
                existing_ids.add(task.id)

        with open(self.backlog_path, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in existing_tasks], f, indent=2, ensure_ascii=False)
        print(f"💾 Progress saved to {self.backlog_path}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"D:\ClawAI\clawai\cognition"
    auditor = BatchAuditor(r"D:\ClawAI")
    auditor.audit_directory(target, chunk_size=50)
