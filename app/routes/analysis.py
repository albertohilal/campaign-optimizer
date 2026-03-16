"""Analysis routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.analyzer import AnalyzerService
from app.services.google_ads_client import GoogleAdsServiceError
from app.services.metrics_service import MetricsService


router = APIRouter(tags=["analysis"])


@router.get("/analysis/snapshot")
def get_analysis_snapshot(date_from: str, date_to: str) -> dict[str, Any]:
    """
    Return a normalized campaign snapshot for the requested date range.

    The snapshot aggregates campaigns, campaign metrics, and search terms
    using MetricsService.
    """

    try:
        metrics_service = MetricsService()
        return metrics_service.get_snapshot(date_from=date_from, date_to=date_to)

    except GoogleAdsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Snapshot data is not available for the current Google Ads configuration.",
        ) from exc


@router.get("/analysis/findings")
def get_analysis_findings(date_from: str, date_to: str) -> dict[str, Any]:
    """
    Return analyzer findings for the requested campaign snapshot date range.

    This endpoint first builds the snapshot through MetricsService and then
    transforms it into findings through AnalyzerService.
    """

    try:
        metrics_service = MetricsService()
        analyzer_service = AnalyzerService()

        snapshot = metrics_service.get_snapshot(date_from=date_from, date_to=date_to)
        return analyzer_service.analyze_snapshot(snapshot)

    except GoogleAdsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Findings data is not available for the current Google Ads configuration.",
        ) from exc