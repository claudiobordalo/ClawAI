from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from clawai.bridge import BridgeParticipantConfig, bridge_service

router = APIRouter()


class BridgeParticipantRequest(BaseModel):
    role: str = Field(default="planner")
    provider: str | None = None
    model: str = ""


class BridgeConsultRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    participants: list[BridgeParticipantRequest] = Field(default_factory=list)
    judge_provider: str | None = None


@router.get("/bridge/providers")
def bridge_providers():
    return {
        "providers": list(bridge_service.available_providers()),
        "tools": list(bridge_service.list_tools()),
        "default_roles": ["planner", "coder", "reviewer"],
    }


@router.post("/bridge/consult")
def bridge_consult(request: BridgeConsultRequest):
    try:
        participants = [
            BridgeParticipantConfig(
                role=item.role,
                provider=item.provider or bridge_service.default_provider_for_role(item.role),
                model=item.model,
            )
            for item in request.participants
        ]
        result = bridge_service.consult(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            participants=participants or None,
            judge_provider=request.judge_provider,
        )
        return asdict(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/bridge/recommend-tool")
def bridge_recommend_tool(request: BridgeConsultRequest):
    try:
        decision = bridge_service.recommend_tool(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            judge_provider=request.judge_provider,
        )
        return asdict(decision)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
