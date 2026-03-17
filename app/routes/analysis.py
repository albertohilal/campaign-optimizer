"""Analysis routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.analyzer import AnalyzerService
from app.services.google_ads_client import GoogleAdsServiceError
from app.services.metrics_service import MetricsService
from app.services.recommendations import RecommendationsService
from app.services.report_generator import ReportGeneratorService


router = APIRouter(tags=["analysis"])


def _build_snapshot_and_findings(
    date_from: str,
    date_to: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return snapshot and analyzer findings for a date range."""

    metrics_service = MetricsService()
    analyzer_service = AnalyzerService()

    snapshot = metrics_service.get_snapshot(date_from=date_from, date_to=date_to)
    findings_payload = analyzer_service.analyze_snapshot(snapshot)
    return snapshot, findings_payload


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
        _, findings_payload = _build_snapshot_and_findings(date_from, date_to)
        return findings_payload

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


@router.get("/analysis/recommendations")
def get_analysis_recommendations(date_from: str, date_to: str) -> dict[str, Any]:
    """Return dry-run recommendations derived from analyzer findings."""

    try:
        _, findings_payload = _build_snapshot_and_findings(date_from, date_to)
        recommendations_service = RecommendationsService()
        return recommendations_service.build_recommendations(
            findings=findings_payload.get("findings", []),
        )

    except GoogleAdsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendations are not available for the current Google Ads configuration.",
        ) from exc


@router.get("/analysis/report")
def get_analysis_report(date_from: str, date_to: str) -> dict[str, Any]:
    """Return a consolidated dry-run report for the requested date range."""

    try:
        snapshot, findings_payload = _build_snapshot_and_findings(date_from, date_to)
        report_generator = ReportGeneratorService()
        return report_generator.generate_report(
            snapshot=snapshot,
            findings_payload=findings_payload,
        )

    except GoogleAdsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report data is not available for the current Google Ads configuration.",
        ) from exc