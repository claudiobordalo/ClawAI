from __future__ import annotations

import importlib
import json
import os
from dataclasses import asdict
from typing import Any

from .auth import load_composio_auth
from .cache import composio_cache
from .models import ComposioConnection, ComposioToolInfo


NATIVE_FALLBACK_TOOLS: tuple[ComposioToolInfo, ...] = (
    ComposioToolInfo(name="git", provider="native", category="devops", description="Git local workspace operations", connected=True, actions=["status", "branch", "commit", "merge_ff_only"]),
    ComposioToolInfo(name="filesystem", provider="native", category="filesystem", description="Repository file inspection and updates", connected=True, actions=["read", "tree", "write"]),
    ComposioToolInfo(name="memory", provider="native", category="memory", description="Semantic memory search and record", connected=True, actions=["search", "remember", "stats"]),
    ComposioToolInfo(name="search", provider="native", category="search", description="Repository search and retrieval", connected=True, actions=["query", "files"]),
    ComposioToolInfo(name="planning", provider="native", category="planning", description="Objective and subtasks planner", connected=True, actions=["analyze", "plan"]),
    ComposioToolInfo(name="workflow", provider="native", category="orchestration", description="Autonomy queue and orchestration", connected=True, actions=["enqueue", "status", "next"]),
)


class ComposioToolDiscovery:
    def __init__(self) -> None:
        self._auth = load_composio_auth()

    def discover_tools(self, force_refresh: bool = False) -> list[ComposioToolInfo]:
        if not force_refresh:
            cached = composio_cache.get("tools")
            if isinstance(cached, list) and cached:
                return [self._tool_from_dict(item) for item in cached if isinstance(item, dict)]

        discovered = self._discover_via_sdk()
        if not discovered:
            discovered = list(NATIVE_FALLBACK_TOOLS)

        composio_cache.set("tools", [asdict(item) for item in discovered])
        return discovered

    def discover_connections(self, force_refresh: bool = False) -> list[ComposioConnection]:
        if not force_refresh:
            cached = composio_cache.get("connections")
            if isinstance(cached, list) and cached:
                return [self._connection_from_dict(item) for item in cached if isinstance(item, dict)]

        discovered = self._discover_connections_via_sdk()
        if not discovered:
            discovered = self._connections_from_env()

        composio_cache.set("connections", [asdict(item) for item in discovered])
        return discovered

    def summary(self) -> dict[str, Any]:
        tools = self.discover_tools()
        connections = self.discover_connections()
        return {
            "configured": self._auth.configured,
            "tools": len(tools),
            "connections": len(connections),
            "providers": sorted({tool.provider for tool in tools}),
            "sample_tools": [tool.name for tool in tools[:10]],
        }

    def _discover_via_sdk(self) -> list[ComposioToolInfo]:
        module = self._import_sdk_module()
        if module is None:
            return []

        client = self._build_sdk_client(module)
        if client is None:
            return []

        for method_name in (
            "discover_tools",
            "list_tools",
            "get_tools",
            "tools",
            "available_tools",
        ):
            method = getattr(client, method_name, None)
            if not callable(method):
                continue
            try:
                raw = method()
            except Exception:
                continue
            normalized = self._normalize_tools(raw)
            if normalized:
                return normalized

        return []

    def _discover_connections_via_sdk(self) -> list[ComposioConnection]:
        module = self._import_sdk_module()
        if module is None:
            return []

        client = self._build_sdk_client(module)
        if client is None:
            return []

        for method_name in (
            "list_connections",
            "connections",
            "get_connections",
        ):
            method = getattr(client, method_name, None)
            if not callable(method):
                continue
            try:
                raw = method()
            except Exception:
                continue
            normalized = self._normalize_connections(raw)
            if normalized:
                return normalized

        return []

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

    def _normalize_tools(self, raw: Any) -> list[ComposioToolInfo]:
        items: list[Any]
        if isinstance(raw, dict):
            for key in ("tools", "items", "data", "results"):
                value = raw.get(key)
                if isinstance(value, list):
                    items = value
                    break
            else:
                items = [raw]
        elif isinstance(raw, list):
            items = raw
        else:
            items = [raw]

        results: list[ComposioToolInfo] = []
        for item in items:
            if isinstance(item, str):
                results.append(ComposioToolInfo(name=item, provider="composio", category="integration", connected=True))
                continue
            if isinstance(item, dict):
                results.append(self._tool_from_dict(item))
        return results

    def _normalize_connections(self, raw: Any) -> list[ComposioConnection]:
        items: list[Any]
        if isinstance(raw, dict):
            for key in ("connections", "items", "data", "results"):
                value = raw.get(key)
                if isinstance(value, list):
                    items = value
                    break
            else:
                items = [raw]
        elif isinstance(raw, list):
            items = raw
        else:
            items = [raw]

        results: list[ComposioConnection] = []
        for item in items:
            if isinstance(item, str):
                results.append(ComposioConnection(toolkit=item, status="unknown"))
                continue
            if isinstance(item, dict):
                results.append(self._connection_from_dict(item))
        return results

    def _connections_from_env(self) -> list[ComposioConnection]:
        raw = os.getenv("COMPOSIO_CONNECTIONS_JSON", "").strip()
        if raw:
            try:
                parsed = json.loads(raw)
                return self._normalize_connections(parsed)
            except Exception:
                pass

        raw = os.getenv("COMPOSIO_CONNECTIONS", "").strip()
        if raw:
            return [
                ComposioConnection(toolkit=item.strip(), status="configured")
                for item in raw.split(",")
                if item.strip()
            ]

        return []

    def _tool_from_dict(self, payload: dict[str, Any]) -> ComposioToolInfo:
        name = str(payload.get("name") or payload.get("tool") or payload.get("slug") or payload.get("id") or "unknown")
        provider = str(payload.get("provider") or payload.get("source") or "composio")
        description = str(payload.get("description") or payload.get("summary") or "")
        connected = bool(payload.get("connected", payload.get("status") in {"connected", "active", True}))
        actions = payload.get("actions")
        if not isinstance(actions, list):
            actions = []
        metadata = {k: v for k, v in payload.items() if k not in {"name", "tool", "slug", "id", "provider", "source", "description", "summary", "connected", "status", "actions"}}
        return ComposioToolInfo(name=name, provider=provider, category=str(payload.get("category") or payload.get("kind") or "integration"), description=description, connected=connected, actions=[str(action) for action in actions], metadata=metadata)

    def _connection_from_dict(self, payload: dict[str, Any]) -> ComposioConnection:
        toolkit = str(payload.get("toolkit") or payload.get("name") or payload.get("slug") or payload.get("id") or "unknown")
        status = str(payload.get("status") or payload.get("state") or "unknown")
        user_id = str(payload.get("user_id") or payload.get("user") or "")
        external_user_id = str(payload.get("external_user_id") or payload.get("externalUserId") or "")
        metadata = {k: v for k, v in payload.items() if k not in {"toolkit", "name", "slug", "id", "status", "state", "user_id", "user", "external_user_id", "externalUserId"}}
        return ComposioConnection(toolkit=toolkit, status=status, user_id=user_id, external_user_id=external_user_id, metadata=metadata)


composio_tool_discovery = ComposioToolDiscovery()
