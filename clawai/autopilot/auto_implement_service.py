from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Iterable

from clawai.ai.router import AIRouter, ModelRole

ROOT = Path(__file__).resolve().parents[2]

IGNORED_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
    ".clawai",
}

CORE_HINT_FILES = [
    "api.py",
    "clawai/chat/chat_service.py",
    "clawai/agents/agent.py",
    "clawai/search/search_engine.py",
    "clawai/ai/router.py",
    "clawai/providers/implementations/ollama_provider.py",
    "clawai/providers/factory/factory.py",
    "clawai/core/config/settings.py",
    "frontend/src/App.tsx",
    "frontend/src/ChatPanel.tsx",
    "frontend/src/api.ts",
    "frontend/src/tree.ts",
    "frontend/src/Explorer.tsx",
]

PREFERRED_EXTENSIONS = {
    ".py",
    ".tsx",
    ".ts",
    ".jsx",
    ".js",
    ".json",
    ".toml",
    ".md",
    ".yml",
    ".yaml",
    ".css",
    ".html",
    ".ini",
    ".cfg",
}

MAX_FILE_CONTEXT_CHARS = 4000
MAX_STDIO_CHARS = 12000


@dataclass(slots=True, frozen=True)
class AutoImplementChange:
    path: str
    status: str
    bytes_written: int = 0
    backup_path: str | None = None


@dataclass(slots=True, frozen=True)
class AutoImplementTestReport:
    command: str
    success: bool
    return_code: int
    stdout: str
    stderr: str
    duration_ms: float


@dataclass(slots=True, frozen=True)
class AutoImplementIteration:
    iteration: int
    summary: str
    changes: list[AutoImplementChange] = field(default_factory=list)
    test: AutoImplementTestReport | None = None


@dataclass(slots=True, frozen=True)
class AutoImplementResult:
    objective: str
    summary: str
    provider: str
    model: str
    candidate_files: list[str]
    iterations: list[AutoImplementIteration]
    success: bool
    test_command: str
    duration_ms: float


class AutoImplementService:
    def __init__(self) -> None:
        self.router = AIRouter()
        self.provider = getattr(self.router, "_provider", "ollama")
        self.model = self.router.model_for(ModelRole.CODER)
        self._lock = Lock()

    def implement(
        self,
        objective: str,
        test_command: str = "uv run python -m pytest -q",
        max_iterations: int = 3,
        max_files: int = 15,
    ) -> AutoImplementResult:
        objective = objective.strip()

        if not objective:
            raise ValueError("objective is required")

        max_iterations = max(1, min(int(max_iterations), 5))
        max_files = max(1, min(int(max_files), 20))

        with self._lock:
            started = time.perf_counter()
            iterations: list[AutoImplementIteration] = []
            seen_candidates: set[str] = set()
            previous_test: AutoImplementTestReport | None = None
            previous_summary = ""
            final_summary = "No changes applied"
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            for iteration in range(1, max_iterations + 1):
                candidate_paths = self._select_candidate_files(
                    objective=objective,
                    previous_test=previous_test,
                    previous_summary=previous_summary,
                    max_files=max_files,
                )

                for path in candidate_paths:
                    seen_candidates.add(path.relative_to(ROOT).as_posix())

                prompt = self._build_prompt(
                    objective=objective,
                    candidate_paths=candidate_paths,
                    iteration=iteration,
                    max_iterations=max_iterations,
                    previous_test=previous_test,
                    previous_summary=previous_summary,
                )

                raw = self.router.ask(
                    prompt,
                    role=ModelRole.CODER,
                    system_prompt=self._system_prompt(),
                )

                plan = self._parse_plan(raw)
                summary = str(plan.get("summary", "")).strip() or f"Iteration {iteration}"
                final_summary = summary

                changes = self._apply_changes(
                    plan.get("changes", []),
                    run_id=run_id,
                    iteration=iteration,
                )

                test_report: AutoImplementTestReport | None = None
                if test_command.strip():
                    test_report = self._run_tests(test_command)

                iterations.append(
                    AutoImplementIteration(
                        iteration=iteration,
                        summary=summary,
                        changes=changes,
                        test=test_report,
                    )
                )

                previous_test = test_report
                previous_summary = self._summarize_iteration(summary, changes, test_report)

                if test_report and test_report.success:
                    break

            duration_ms = (time.perf_counter() - started) * 1000
            success = bool(
                iterations
                and iterations[-1].test is not None
                and iterations[-1].test.success
            )

            return AutoImplementResult(
                objective=objective,
                summary=final_summary,
                provider=self.provider,
                model=self.model,
                candidate_files=sorted(seen_candidates),
                iterations=iterations,
                success=success,
                test_command=test_command,
                duration_ms=duration_ms,
            )

    def _system_prompt(self) -> str:
        return (
            "Você é o mecanismo de auto-implementação do ClawAI.\n"
            "Retorne APENAS um JSON válido, sem markdown, sem blocos de código e sem explicações.\n"
            "Esquema esperado:\n"
            '{\n'
            '  "summary": "resumo curto",\n'
            '  "changes": [\n'
            '    {\n'
            '      "path": "caminho/relativo/ao/repo.ext",\n'
            '      "content": "conteúdo completo do arquivo"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Regras:\n"
            "- Use apenas caminhos relativos ao root do repositório.\n"
            "- Se um arquivo não precisa mudar, não o inclua.\n"
            "- Quando mudar um arquivo, forneça o conteúdo completo final do arquivo.\n"
            "- Faça mudanças mínimas e preservando a arquitetura existente.\n"
            "- Se houver falhas de teste anteriores, corrija-as primeiro.\n"
            "- Se não houver mudanças necessárias, retorne changes como lista vazia.\n"
        )

    def _iter_repo_files(self) -> Iterable[Path]:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue

            if any(part in IGNORED_NAMES for part in path.parts):
                continue

            yield path

    def _normalize_path_text(self, value: str) -> str:
        text = value.replace("\\", "/").lower()
        root_text = ROOT.as_posix().replace("\\", "/").lower()

        if root_text in text:
            text = text.split(root_text, 1)[1].lstrip("/")

        return text

    def _extract_path_hints(self, text: str) -> set[str]:
        hints: set[str] = set()

        matches = re.findall(
            r"[A-Za-z0-9_./\\-]+\.(?:py|pyi|tsx|ts|jsx|js|json|toml|md|ya?ml|cfg|ini|css|html)",
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            normalized = self._normalize_path_text(match)
            if normalized:
                hints.add(normalized)

        return hints

    def _tokenize(self, text: str) -> set[str]:
        tokens = {
            token.lower()
            for token in re.findall(r"[A-Za-z0-9_]+", text)
            if len(token) >= 3
        }
        return tokens

    def _score_path(
        self,
        path: Path,
        objective_tokens: set[str],
        path_hints: set[str],
    ) -> int:
        rel_text = path.relative_to(ROOT).as_posix().lower()
        score = 0

        if path.name in {
            "api.py",
            "package.json",
            "pyproject.toml",
            "README.md",
            "pytest.ini",
        }:
            score += 12

        if path.suffix.lower() in PREFERRED_EXTENSIONS:
            score += 3

        if rel_text.startswith("clawai/"):
            score += 4
        if rel_text.startswith("frontend/"):
            score += 4
        if rel_text.startswith("tests/"):
            score += 3

        for token in objective_tokens:
            if token in rel_text:
                score += 4
            if token in path.name.lower():
                score += 2

        for hint in path_hints:
            if hint in rel_text:
                score += 8
            if hint in path.name.lower():
                score += 4

        return score

    def _select_candidate_files(
        self,
        objective: str,
        previous_test: AutoImplementTestReport | None,
        previous_summary: str,
        max_files: int,
    ) -> list[Path]:
        seed_text = objective
        if previous_summary:
            seed_text += "\n" + previous_summary
        if previous_test:
            seed_text += "\n" + previous_test.stdout + "\n" + previous_test.stderr

        objective_tokens = self._tokenize(seed_text)
        path_hints = self._extract_path_hints(seed_text)

        selected: list[Path] = []
        selected_set: set[str] = set()

        for hint in CORE_HINT_FILES:
            path = ROOT / hint
            if path.exists() and path.is_file():
                rel = path.relative_to(ROOT).as_posix()
                if rel not in selected_set:
                    selected.append(path)
                    selected_set.add(rel)

        scored: list[tuple[int, str, Path]] = []
        for path in self._iter_repo_files():
            rel = path.relative_to(ROOT).as_posix()
            if rel in selected_set:
                continue

            score = self._score_path(path, objective_tokens, path_hints)
            if score <= 0:
                continue

            scored.append((score, rel.lower(), path))

        scored.sort(key=lambda item: (-item[0], item[1]))

        for _, rel, path in scored:
            if len(selected) >= max_files:
                break
            if rel not in selected_set:
                selected.append(path)
                selected_set.add(rel)

        return selected[:max_files]

    def _read_file_snippet(self, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            return f"[Falha ao ler arquivo: {exc}]"

        if len(content) <= MAX_FILE_CONTEXT_CHARS:
            return content

        return content[:MAX_FILE_CONTEXT_CHARS] + "\n\n[TRUNCATED]"

    def _build_prompt(
        self,
        objective: str,
        candidate_paths: list[Path],
        iteration: int,
        max_iterations: int,
        previous_test: AutoImplementTestReport | None,
        previous_summary: str,
    ) -> str:
        parts: list[str] = [
            f"Objetivo:\n{objective}\n",
            f"Iteração atual: {iteration}/{max_iterations}\n",
        ]

        if previous_summary:
            parts.append(f"Resumo da iteração anterior:\n{previous_summary}\n")

        if previous_test:
            parts.append(
                "Resultado do teste anterior:\n"
                f"Comando: {previous_test.command}\n"
                f"Sucesso: {previous_test.success}\n"
                f"Return code: {previous_test.return_code}\n\n"
                "STDOUT:\n"
                f"{previous_test.stdout}\n\n"
                "STDERR:\n"
                f"{previous_test.stderr}\n"
            )

        parts.append(
            "Arquivos relevantes atuais:\n"
        )

        for path in candidate_paths:
            rel = path.relative_to(ROOT).as_posix()
            snippet = self._read_file_snippet(path)
            parts.append(
                f'<file path="{rel}">\n'
                f"{snippet}\n"
                f"</file>\n"
            )

        parts.append(
            "\nTarefa:\n"
            "Use os arquivos acima para implementar a mudança pedida.\n"
            "Retorne somente o JSON final com summary e changes.\n"
            "Cada change deve conter o path relativo e o conteúdo completo do arquivo final.\n"
        )

        return "\n".join(parts)

    def _extract_json(self, raw: str) -> dict[str, object]:
        text = raw.strip()

        fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.S)
        if fence:
            text = fence.group(1).strip()
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]

        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("AutoImplement response must be a JSON object")

        return data

    def _resolve_relative_path(self, rel_path: str) -> Path:
        target = (ROOT / rel_path).resolve()
        if target != ROOT and ROOT not in target.parents:
            raise ValueError(f"Invalid path outside repository: {rel_path}")
        return target

    def _apply_changes(
        self,
        changes: object,
        run_id: str,
        iteration: int,
    ) -> list[AutoImplementChange]:
        if not isinstance(changes, list):
            raise ValueError("AutoImplement response 'changes' must be a list")

        iteration_backup_root = (
            ROOT
            / ".clawai"
            / "autobackups"
            / run_id
            / f"iter_{iteration:02d}"
        )

        applied: list[AutoImplementChange] = []

        for item in changes:
            if not isinstance(item, dict):
                raise ValueError("Each change must be an object")

            rel_path = str(item.get("path", "")).strip()
            content = item.get("content")

            if not rel_path:
                raise ValueError("Change path is required")

            if not isinstance(content, str):
                raise ValueError(f"Change content for {rel_path!r} must be a string")

            target = self._resolve_relative_path(rel_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            existing = None
            if target.exists():
                try:
                    existing = target.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    existing = None

            if existing == content:
                applied.append(
                    AutoImplementChange(
                        path=rel_path,
                        status="unchanged",
                        bytes_written=len(content.encode("utf-8")),
                        backup_path=None,
                    )
                )
                continue

            backup_path = None
            if target.exists():
                backup_path = iteration_backup_root / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup_path)

            target.write_text(content, encoding="utf-8")

            applied.append(
                AutoImplementChange(
                    path=rel_path,
                    status="written",
                    bytes_written=len(content.encode("utf-8")),
                    backup_path=backup_path.as_posix() if backup_path else None,
                )
            )

        return applied

    def _trim(self, text: str) -> str:
        if len(text) <= MAX_STDIO_CHARS:
            return text
        return text[:MAX_STDIO_CHARS] + "\n\n[TRUNCATED]"

    def _run_tests(self, command: str) -> AutoImplementTestReport:
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=str(ROOT),
                shell=True,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            duration_ms = (time.perf_counter() - started) * 1000

            return AutoImplementTestReport(
                command=command,
                success=completed.returncode == 0,
                return_code=completed.returncode,
                stdout=self._trim(completed.stdout or ""),
                stderr=self._trim(completed.stderr or ""),
                duration_ms=duration_ms,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            stdout = self._trim(getattr(exc, "stdout", "") or "")
            stderr = self._trim(getattr(exc, "stderr", "") or "")

            return AutoImplementTestReport(
                command=command,
                success=False,
                return_code=124,
                stdout=stdout,
                stderr=(stderr or "") + "\nTimed out after 1800 seconds.",
                duration_ms=duration_ms,
            )

    def _summarize_iteration(
        self,
        summary: str,
        changes: list[AutoImplementChange],
        test: AutoImplementTestReport | None,
    ) -> str:
        change_lines = [f"- {change.path} ({change.status})" for change in changes]
        test_line = "Teste não executado"
        if test is not None:
            test_line = f"Teste: {'sucesso' if test.success else 'falhou'} ({test.return_code})"

        return "\n".join(
            [
                f"Resumo: {summary}",
                test_line,
                "Alterações:",
                *change_lines if change_lines else ["- nenhuma"],
            ]
        )

    def _parse_plan(self, raw: str) -> dict[str, object]:
        try:
            return self._extract_json(raw)
        except Exception as exc:
            raise ValueError(f"Falha ao interpretar JSON do modelo: {exc}") from exc


auto_implement = AutoImplementService()