"""Services for preparing campaign metrics snapshots."""

from __future__ import annotations

from typing import Any

from app.services.google_ads_client import GoogleAdsClientService


class MetricsService:
    """Prepare normalized campaign snapshot data for analysis flows."""

    def __init__(self) -> None:
        """Initialize the metrics service with the Google Ads client wrapper."""

        self.google_ads_client = GoogleAdsClientService()

    def get_snapshot(self, date_from: str, date_to: str) -> dict[str, Any]:
        """Return a normalized snapshot of campaigns, metrics, and search terms."""

        campaigns = self.google_ads_client.get_campaigns()
        campaign_metrics = self.google_ads_client.get_campaign_metrics(
            date_from=date_from,
            date_to=date_to,
        )
        search_terms = self.google_ads_client.get_search_terms(
            date_from=date_from,
            date_to=date_to,
        )

        return {
            "date_from": date_from,
            "date_to": date_to,
            "campaigns": campaigns,
            "campaign_metrics": campaign_metrics,
            "search_terms": search_terms,
        }