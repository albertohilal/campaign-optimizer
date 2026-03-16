"""Analysis routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.google_ads_client import GoogleAdsServiceError
from app.services.metrics_service import MetricsService


router = APIRouter(tags=["analysis"])


@router.get("/analysis/snapshot")
def get_analysis_snapshot(date_from: str, date_to: str) -> dict[str, Any]:
    """
    Return a campaign metrics snapshot for the given date range.

    This endpoint aggregates campaign data, metrics, and search terms
    using the MetricsService.
    """

    try:
        service = MetricsService()
        return service.get_snapshot(date_from=date_from, date_to=date_to)

    except GoogleAdsServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=503,
            detail="Snapshot data is not available for the current Google Ads configuration.",
        ) from exc