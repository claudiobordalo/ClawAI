from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from clawai.integrations.composio import composio_service
from clawai.integrations.composio.models import ComposioExecutionRequest
from clawai.intelligence.broker import cognition_broker, intelligence_orchestrator

router = APIRouter()


class IntelligenceAnalyzeRequest(BaseModel):
    prompt: str
    objective: str | None = None


class IntelligenceRememberRequest(BaseModel):
    objective: str
    prompt: str
    summary: str
    tool: str = ""
    outcome: str = ""
    tags: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComposioExecuteRequest(BaseModel):
    tool_name: str
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    provider: str | None = None


@router.get("/intelligence/state")
def intelligence_state():
    return intelligence_orchestrator.state()


@router.post("/intelligence/analyze")
def intelligence_analyze(request: IntelligenceAnalyzeRequest):
    try:
        return asdict(intelligence_orchestrator.analyze(request.prompt, request.objective))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/intelligence/tools")
def intelligence_tools(force_refresh: bool = False):
    return [asdict(item) for item in cognition_broker.discover_tools(force_refresh=force_refresh)]


@router.get("/intelligence/memory/search")
def intelligence_memory_search(query: str, limit: int = 10):
    return [entry.to_dict() for entry in cognition_broker.search_memory(query, limit=limit)]


@router.post("/intelligence/memory/remember")
def intelligence_memory_remember(request: IntelligenceRememberRequest):
    try:
        entry = intelligence_orchestrator.learn_from_execution(
            objective=request.objective,
            prompt=request.prompt,
            summary=request.summary,
            tool=request.tool,
            outcome=request.outcome,
            artifacts=request.artifacts,
            tags=request.tags,
            metadata=request.metadata,
        )
        return entry.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/integrations/composio/status")
def composio_status():
    return composio_service.summary()


@router.get("/integrations/composio/tools")
def composio_tools(force_refresh: bool = False):
    return [asdict(item) for item in composio_service.discover_tools(force_refresh=force_refresh)]


@router.get("/integrations/composio/connections")
def composio_connections(force_refresh: bool = False):
    return [asdict(item) for item in composio_service.connections(force_refresh=force_refresh)]


@router.post("/integrations/composio/execute")
def composio_execute(request: ComposioExecuteRequest):
    try:
        return asdict(
            composio_service.execute(
                ComposioExecutionRequest(
                    tool_name=request.tool_name,
                    action=request.action,
                    parameters=request.parameters,
                    provider=request.provider or "composio",
                )
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
