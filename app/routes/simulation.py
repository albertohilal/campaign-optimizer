from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulate", tags=["simulation"])


class SimulationRequest(BaseModel):
    findings: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)


@router.post("")
def simulate(payload: SimulationRequest) -> dict[str, Any]:
    service = SimulationService()
    return service.simulate(
        findings=payload.findings,
        actions=payload.actions,
    )