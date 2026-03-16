"""Campaign routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.google_ads_client import (
    GoogleAdsClientService,
    GoogleAdsServiceError,
)


router = APIRouter(tags=["campaigns"])


@router.get("/campaigns")
def list_campaigns() -> list[dict[str, object]]:
    """Return campaign data from Google Ads or mock fixtures."""

    try:
        service = GoogleAdsClientService()
        return service.get_campaigns()
    except GoogleAdsServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc