from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from clawai.editor import EditOperation
from clawai.codebase.project_snapshot import ProjectSnapshot


@dataclass(frozen=True)
class ProviderOperation:
    file: str
    reason: str
    new_content: str


class PatchPlanner:
    """Transforms a ChangeRequest into a PatchPlan using analyzer, retriever, prompt engine and provider.

    Flow: ChangeRequest -> CodeAnalyzer -> ContextRetriever -> PromptEngine -> Provider -> PatchPlan

    This component never writes to disk and never applies edits.
    """

    def __init__(
        self,
        *,
        context_retriever: Any,
        code_analyzer: Any,
        llm_planner: Any,
        prompt_engine: Any,
        provider: Any,
    ) -> None:
        # Store dependencies; types are duck-typed for loose coupling and testing.
        self._retriever = context_retriever
        self._analyzer = code_analyzer
        self._llm_planner = llm_planner
        self._prompt_engine = prompt_engine
        self._provider = provider

    def plan(self, request: Any, project_root: str | Path):
        from .patch_plan import PatchPlan  # local import to avoid cycles
        try:
            # Basic validation
            if request is None:
                return PatchPlan.error_plan("ChangeRequest ausente.")
            obj = getattr(request, "objective", None)
            tgt = getattr(request, "target_query", None)
            instr = getattr(request, "instructions", None)
            if not isinstance(obj, str) or not obj.strip():
                return PatchPlan.error_plan("objective inválido.")
            if not isinstance(tgt, str) or not tgt.strip():
                return PatchPlan.error_plan("target_query inválido.")
            if not isinstance(instr, str) or not instr.strip():
                return PatchPlan.error_plan("instructions inválido.")

            root = Path(project_root).resolve()

            # Analyze project and retrieve context
            snapshot: ProjectSnapshot = self._analyzer.analyze(root)
            retrieval = self._retriever.retrieve(snapshot, tgt.strip())

            # If no relevant files, short-circuit with deterministic error
            files_from_context: Tuple[str, ...] = getattr(retrieval, "files", tuple()) or tuple()
            if len(files_from_context) == 0:
                return PatchPlan.error_plan("Nenhum arquivo relevante encontrado para o target_query.")

            # Build deterministic prompt
            sorted_files = tuple(sorted(files_from_context))
            user_prompt = self._build_user_prompt(obj.strip(), instr.strip(), sorted_files)

            # Execute via PromptEngine (it will delegate to the provider). Never let exceptions escape
            try:
                content: str = self._prompt_engine.execute("system", user_prompt)
            except Exception as pe:
                return PatchPlan.error_plan(f"Provider/PromptEngine falhou: {pe}")

            # Parse provider JSON strictly
            parsed = self._parse_provider_json(content)
            if isinstance(parsed, str):  # error message
                return PatchPlan.error_plan(parsed)

            summary, provider_ops = parsed

            # Map snapshot files: relative path (posix) -> absolute
            snapshot_map: Dict[str, Path] = {}
            root_path = Path(snapshot.root).resolve()
            for sf in snapshot.files:
                abs_path = Path(sf.path).resolve()
                try:
                    rel = abs_path.relative_to(root_path)
                except Exception:
                    # If file is outside root, skip (shouldn't happen with analyzer implementation)
                    continue
                key = str(rel).replace("\\", "/")
                snapshot_map[key] = abs_path

            operations: List[EditOperation] = []
            for op in provider_ops:
                rel = op.file.strip().replace("\\", "/")
                if rel not in snapshot_map:
                    return PatchPlan.error_plan(f"Arquivo não localizado no snapshot: {op.file}")
                file_path = snapshot_map[rel]
                try:
                    original = file_path.read_text(encoding="utf-8")
                except Exception as re:
                    return PatchPlan.error_plan(f"Falha ao ler conteúdo original de {file_path}: {re}")

                operations.append(
                    EditOperation(
                        file=str(file_path),
                        original_content=original,
                        new_content=op.new_content,
                        reason=op.reason,
                    )
                )

            return PatchPlan.success_plan(tuple(operations), summary)
        except Exception as e:
            return PatchPlan.error_plan(f"PatchPlanner erro inesperado: {e}")

    def _build_user_prompt(self, objective: str, instructions: str, files: Tuple[str, ...]) -> str:
        lines: List[str] = [
            "Você é um planejador de patches.",
            "Gere uma proposta de alterações no formato JSON especificado.",
            "Retorne APENAS JSON válido.",
            "Arquivos de contexto (relativos ao root):",
        ]
        for f in files:
            lines.append(f"- {f}")
        lines.extend(
            [
                "",
                "Objetivo:",
                objective,
                "",
                "Instruções:",
                instructions,
                "",
                "Formato esperado:",
                '{"summary": "...", "operations": [{"file": "...", "reason": "...", "new_content": "..."}]}',
            ]
        )
        return "\n".join(lines)

    def _parse_provider_json(self, content: str):
        try:
            if not isinstance(content, str) or not content.strip():
                return "Resposta vazia do provider."
            data = json.loads(content.strip())
        except json.JSONDecodeError:
            return "JSON inválido retornado pelo provider."
        if not isinstance(data, dict):
            return "JSON do provider deve ser um objeto."
        summary = data.get("summary")
        ops = data.get("operations")
        if not isinstance(summary, str):
            return "Campo 'summary' inválido."
        if not isinstance(ops, list):
            return "Campo 'operations' deve ser uma lista."
        provider_ops: List[ProviderOperation] = []
        for idx, item in enumerate(ops):
            if not isinstance(item, dict):
                return f"Operação #{idx+1} inválida (deve ser objeto)."
            f = item.get("file")
            r = item.get("reason")
            n = item.get("new_content")
            if not isinstance(f, str) or not f.strip():
                return f"Operação #{idx+1}: campo 'file' inválido."
            if not isinstance(r, str) or not r.strip():
                return f"Operação #{idx+1}: campo 'reason' inválido."
            if not isinstance(n, str):
                return f"Operação #{idx+1}: campo 'new_content' inválido."
            provider_ops.append(ProviderOperation(file=f.strip(), reason=r.strip(), new_content=n))
        return summary, tuple(provider_ops)
