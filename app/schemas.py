"""Pydantic schemas used by the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Response payload for the root endpoint."""

    app_name: str
    message: str
    phase: str
    docs_url: str
    mock_mode_ready: bool


class HealthResponse(BaseModel):
    """Response payload for the health endpoint."""

    status: str
    app_name: str
    environment: str
    database: str


class FindingItem(BaseModel):
    """Structured finding item for analysis payloads."""

    code: str
    severity: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationItem(BaseModel):
    """Structured recommendation item for analysis payloads."""

    title: str
    detail: str
    priority: str = "medium"


class AnalysisReportBase(BaseModel):
    """Shared analysis report fields."""

    customer_id: str
    account_name: str
    period_label: str
    summary: str
    findings: list[FindingItem] = Field(default_factory=list)
    recommendations: list[RecommendationItem] = Field(default_factory=list)


class AnalysisReportCreate(AnalysisReportBase):
    """Schema used to create a new analysis report."""

    pass


class AnalysisReportResponse(AnalysisReportBase):
    """Stored analysis report response."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}