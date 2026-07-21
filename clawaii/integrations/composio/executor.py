from __future__ import annotations

import importlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .auth import load_composio_auth
from .cache import composio_cache
from .models import ComposioExecutionRequest, ComposioExecutionResult

ROOT = Path(__file__).resolve().parents[3]


@dataclass(slots=True)
class NativeExecutionResult:
    success: bool
    output: Any = None
    error: str = ""


class ComposioExecutor:
    def __init__(self) -> None:
        self._auth = load_composio_auth()

    def execute(self, request: ComposioExecutionRequest) -> ComposioExecutionResult:
        started_at = time.perf_counter()
        try:
            native = self._execute_native(request)
            if native is not None:
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                return ComposioExecutionResult(
                    success=native.success,
                    tool_name=request.tool_name,
                    action=request.action,
                    provider=request.provider,
                    output=native.output,
                    error=native.error,
                    elapsed_ms=elapsed_ms,
                    metadata={"mode": "native"},
                )

            sdk_result = self._execute_sdk(request)
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            if sdk_result is not None:
                return sdk_result

            return ComposioExecutionResult(
                success=False,
                tool_name=request.tool_name,
                action=request.action,
                provider=request.provider,
                error="No native or SDK executor available for this request.",
                elapsed_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            return ComposioExecutionResult(
                success=False,
                tool_name=request.tool_name,
                action=request.action,
                provider=request.provider,
                error=str(exc),
                elapsed_ms=elapsed_ms,
            )

    def _execute_native(self, request: ComposioExecutionRequest) -> NativeExecutionResult | None:
        tool = request.tool_name.lower()
        action = request.action.lower()
        args = request.parameters

        if tool in {"filesystem", "files", "file"}:
            return self._filesystem(action, args)
        if tool == "search":
            return self._search(action, args)
        if tool == "memory":
            return self._memory(action, args)
        if tool == "git":
            return self._git(action, args)
        if tool == "verify":
            return self._verify()
        if tool == "chat":
            return NativeExecutionResult(success=False, error="Chat is model-driven and should be executed through the bridge.")
        return None

    def _filesystem(self, action: str, args: dict[str, Any]) -> NativeExecutionResult:
        path = str(args.get("path", "")).strip()
        target = (ROOT / path).resolve() if path else ROOT
        if target != ROOT and ROOT not in target.parents:
            return NativeExecutionResult(success=False, error="Invalid path")

        if action in {"read", "get", "open"}:
            if not target.exists() or not target.is_file():
                return NativeExecutionResult(success=False, error="File not found")
            return NativeExecutionResult(success=True, output=target.read_text(encoding="utf-8", errors="ignore"))

        if action in {"tree", "list", "ls"}:
            if not target.exists() or not target.is_dir():
                return NativeExecutionResult(success=False, error="Folder not found")
            return NativeExecutionResult(
                success=True,
                output=[
                    {
                        "name": child.name,
                        "path": str(child.relative_to(ROOT)).replace("\\", "/"),
                        "directory": child.is_dir(),
                    }
                    for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                ],
            )

        if action in {"write", "save", "set"}:
            content = str(args.get("content", ""))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return NativeExecutionResult(success=True, output={"path": str(target.relative_to(ROOT)).replace("\\", "/"), "bytes": len(content.encode("utf-8"))})

        return NativeExecutionResult(success=False, error=f"Unsupported filesystem action: {action}")

    def _search(self, action: str, args: dict[str, Any]) -> NativeExecutionResult:
        query = str(args.get("query") or args.get("text") or "").strip().lower()
        if not query:
            return NativeExecutionResult(success=False, error="query is required")

        limit = int(args.get("limit", 20))
        matches: list[dict[str, Any]] = []
        for path in ROOT.rglob("*"):
            if len(matches) >= limit:
                break
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if query in text.lower() or query in path.name.lower() or query in str(path).lower():
                matches.append({
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "score": 1.0,
                    "preview": text[:300],
                })
        return NativeExecutionResult(success=True, output=matches)

    def _memory(self, action: str, args: dict[str, Any]) -> NativeExecutionResult:
        try:
            from clawai.intelligence.memory import semantic_memory
        except Exception as exc:
            return NativeExecutionResult(success=False, error=str(exc))

        if action in {"search", "find"}:
            query = str(args.get("query") or args.get("text") or "").strip()
            return NativeExecutionResult(success=True, output=[entry.to_dict() for entry in semantic_memory.search(query, limit=int(args.get("limit", 10)))])
        if action in {"remember", "add", "record"}:
            payload = args.get("payload")
            if not isinstance(payload, dict):
                return NativeExecutionResult(success=False, error="payload must be a dict")
            semantic_memory.remember(payload)
            return NativeExecutionResult(success=True, output={"stored": True})
        if action in {"stats", "summary"}:
            return NativeExecutionResult(success=True, output=semantic_memory.stats())
        return NativeExecutionResult(success=False, error=f"Unsupported memory action: {action}")

    def _git(self, action: str, args: dict[str, Any]) -> NativeExecutionResult:
        command = [sys.executable, "-c", "print('git adapter unavailable in native executor')"]
        if action == "status":
            command = ["git", "-C", str(ROOT), "status", "--short"]
        elif action == "branch":
            command = ["git", "-C", str(ROOT), "branch", "--show-current"]
        elif action == "commit":
            message = str(args.get("message") or "ClawAI auto commit")
            command = ["git", "-C", str(ROOT), "add", "-A", "&&", "git", "-C", str(ROOT), "commit", "--allow-empty", "-m", message]
            return self._shell(command)
        elif action in {"merge", "merge_ff_only"}:
            target = str(args.get("target") or args.get("branch") or "")
            source = str(args.get("source") or args.get("from") or "")
            if not target or not source:
                return NativeExecutionResult(success=False, error="target/source required")
            return self._shell(["git", "-C", str(ROOT), "checkout", target, "&&", "git", "-C", str(ROOT), "merge", "--ff-only", source])
        else:
            return NativeExecutionResult(success=False, error=f"Unsupported git action: {action}")
        return self._run(command)

    def _verify(self) -> NativeExecutionResult:
        command = [sys.executable, "verify.py"]
        completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
        return NativeExecutionResult(success=completed.returncode == 0, output={"stdout": completed.stdout, "stderr": completed.stderr, "return_code": completed.returncode})

    def _run(self, command: list[str]) -> NativeExecutionResult:
        completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True)
        return NativeExecutionResult(success=completed.returncode == 0, output={"stdout": completed.stdout, "stderr": completed.stderr, "return_code": completed.returncode})

    def _shell(self, command: list[str]) -> NativeExecutionResult:
        joined = " ".join(command)
        completed = subprocess.run(joined, cwd=str(ROOT), capture_output=True, text=True, shell=True)
        return NativeExecutionResult(success=completed.returncode == 0, output={"stdout": completed.stdout, "stderr": completed.stderr, "return_code": completed.returncode, "command": joined})

    def _execute_sdk(self, request: ComposioExecutionRequest) -> ComposioExecutionResult | None:
        module = self._import_sdk_module()
        if module is None:
            return None

        client = self._build_sdk_client(module)
        if client is None:
            return None

        payload = dict(request.parameters)
        for method_name in (
            "execute",
            "run_action",
            "invoke",
            "call_action",
            "trigger",
        ):
            method = getattr(client, method_name, None)
            if not callable(method):
                continue
            try:
                response = method(tool=request.tool_name, action=request.action, parameters=payload)
            except TypeError:
                try:
                    response = method(request.tool_name, request.action, payload)
                except Exception:
                    continue
            except Exception as exc:
                return ComposioExecutionResult(
                    success=False,
                    tool_name=request.tool_name,
                    action=request.action,
                    provider=request.provider,
                    error=str(exc),
                )
            return ComposioExecutionResult(
                success=True,
                tool_name=request.tool_name,
                action=request.action,
                provider=request.provider,
                output=response,
                metadata={"mode": "sdk", "method": method_name},
            )
        return None

    def _import_sdk_module(self) -> Any | None:
        try:
            return importlib.import_module("composio")
        except Exception:
            return None

    def _build_sdk_client(self, module: Any) -> Any | None:
        for attr in ("ComposioToolSet", "Composio", "ToolSet", "Client"):
            client_cls = getattr(module, attr, None)
            if client_cls is None:
                continue
            try:
                kwargs: dict[str, Any] = {}
                if self._auth.api_key:
                    kwargs["api_key"] = self._auth.api_key
                if self._auth.base_url:
                    kwargs["base_url"] = self._auth.base_url
                if self._auth.client_id:
                    kwargs["client_id"] = self._auth.client_id
                if self._auth.client_secret:
                    kwargs["client_secret"] = self._auth.client_secret
                if self._auth.workspace_id:
                    kwargs["workspace_id"] = self._auth.workspace_id
                return client_cls(**kwargs)
            except Exception:
                continue
        return None


composio_executor = ComposioExecutor()
