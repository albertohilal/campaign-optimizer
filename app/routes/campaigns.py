"""Campaign routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.analyzer import AnalyzerService
from app.services.google_ads_client import (
    GoogleAdsClientService,
    GoogleAdsServiceError,
)
from app.services.metrics_service import MetricsService
from app.services.recommendations import RecommendationsService
from app.services.report_generator import ReportGeneratorService
from app.services.simulation_service import SimulationService


router = APIRouter(tags=["campaigns"])


@router.get("/campaigns")
def list_campaigns() -> list[dict[str, object]]:
    """Return campaign data from Google Ads or mock fixtures."""

    try:
        service = GoogleAdsClientService()
        return service.get_campaigns()
    except GoogleAdsServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/campaigns/{campaign_id}/report")
def get_campaign_report(
    campaign_id: str,
    date_from: str,
    date_to: str,
) -> dict[str, Any]:
    """Return a consolidated dry-run report for a single campaign."""

    try:
        metrics_service = MetricsService()
        analyzer_service = AnalyzerService()
        simulation_service = SimulationService()
        recommendations_service = RecommendationsService(
            simulation_service=simulation_service,
        )
        report_generator = ReportGeneratorService(
            recommendations_service=recommendations_service,
            simulation_service=simulation_service,
        )

        snapshot = metrics_service.get_campaign_snapshot(
            campaign_id=campaign_id,
            date_from=date_from,
            date_to=date_to,
        )

        if not snapshot.get("campaigns"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign '{campaign_id}' was not found for the requested report scope.",
            )

        findings_payload = analyzer_service.analyze_snapshot(snapshot)
        simulation_payload = simulation_service.simulate(
            findings=findings_payload.get("findings", []),
        )
        recommendations_payload = recommendations_service.build_recommendations(
            findings=findings_payload.get("findings", []),
            simulation=simulation_payload,
        )
        report_payload = report_generator.generate_report(
            snapshot=snapshot,
            findings_payload=findings_payload,
            recommendations_payload=recommendations_payload,
            simulation_payload=simulation_payload,
        )

        report_payload["campaign_id"] = campaign_id
        return report_payload

    except GoogleAdsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign report data is not available for the current Google Ads configuration.",
        ) from exc