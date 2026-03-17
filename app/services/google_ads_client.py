"""Google Ads client wrapper for campaign data access."""

from __future__ import annotations

from typing import Any

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from app.config import Settings, get_settings
from app.logger import get_logger


GAQL_CAMPAIGNS_QUERY = """
    SELECT
      campaign.id,
      campaign.name,
      campaign.status,
      campaign.advertising_channel_type
    FROM campaign
    ORDER BY campaign.id
"""

GAQL_CAMPAIGN_METRICS_QUERY = """
        SELECT
            segments.date,
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.ctr,
            metrics.average_cpc,
            metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
            AND campaign.status != 'REMOVED'
        ORDER BY segments.date, campaign.id
"""

GAQL_SEARCH_TERMS_QUERY = """
        SELECT
            segments.date,
            campaign.id,
            campaign.name,
            search_term_view.search_term,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
            AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC, search_term_view.search_term
"""


class GoogleAdsServiceError(Exception):
    """Controlled application error for Google Ads service failures."""


class GoogleAdsClientService:
    """Wrap the official Google Ads client with app-specific safeguards."""

    def __init__(self) -> None:
        """Initialize settings, logger, and real or mock client mode."""

        self.settings: Settings = get_settings()
        self.logger = get_logger(__name__)
        self.mock_mode = self.settings.mock_google_ads_mode
        self.client: GoogleAdsClient | None = None

        if self.mock_mode:
            self.logger.info(
                "Google Ads mock mode enabled because credentials are missing in development."
            )
            return

        self._validate_credentials()
        self.client = self._build_client()

    def _validate_credentials(self) -> None:
        """Validate that the minimum required credentials are configured."""

        if self.settings.google_ads_credentials_present:
            return

        raise GoogleAdsServiceError(
            "Google Ads credentials are incomplete. Set all required environment variables or use development mode for automatic mock data."
        )

    def _build_client(self) -> GoogleAdsClient:
        """Build the official Google Ads client from environment-backed settings."""

        config: dict[str, Any] = {
            "developer_token": self.settings.google_ads_developer_token,
            "client_id": self.settings.google_ads_client_id,
            "client_secret": self.settings.google_ads_client_secret,
            "refresh_token": self.settings.google_ads_refresh_token,
            "use_proto_plus": True,
        }

        if self.settings.google_ads_login_customer_id:
            config["login_customer_id"] = self.settings.google_ads_login_customer_id

        try:
            return GoogleAdsClient.load_from_dict(config)
        except GoogleAdsException as exc:
            self.logger.exception("Google Ads client initialization failed.")
            raise GoogleAdsServiceError(
                "Failed to initialize Google Ads client. Verify the developer token and OAuth credentials."
            ) from exc
        except Exception as exc:
            self.logger.exception("Unexpected error while initializing Google Ads client.")
            raise GoogleAdsServiceError(
                "Unable to initialize Google Ads client. Check environment configuration and library setup."
            ) from exc

    def _get_mock_campaigns(self) -> list[dict[str, object]]:
        """Return realistic sample campaigns for development mode."""

        return [
            {
                "campaign_id": "1001",
                "campaign_name": "Tabiques Sanitarios - Búsqueda",
                "status": "ENABLED",
                "advertising_channel_type": "SEARCH",
            },
            {
                "campaign_id": "1002",
                "campaign_name": "Divisiones para Baños - Search",
                "status": "ENABLED",
                "advertising_channel_type": "SEARCH",
            },
            {
                "campaign_id": "1003",
                "campaign_name": "Divisiones de Oficina - Search",
                "status": "PAUSED",
                "advertising_channel_type": "SEARCH",
            },
            {
                "campaign_id": "1004",
                "campaign_name": "Boxes Sanitarios - Leads",
                "status": "ENABLED",
                "advertising_channel_type": "SEARCH",
            },
        ]

    def _get_mock_campaign_metrics(self) -> list[dict[str, object]]:
        """Return sample campaign metrics for development mode."""

        return [
            {
                "date": "2026-03-17",
                "campaign_id": "1001",
                "campaign_name": "Tabiques Sanitarios - Búsqueda",
                "clicks": 50,
                "impressions": 753,
                "cost_micros": 8215880000,
                "ctr": 6.64,
                "average_cpc": 164.32,
                "cost": 8215.88,
                "conversions": 1.05,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1002",
                "campaign_name": "Divisiones para Baños - Search",
                "clicks": 54,
                "impressions": 700,
                "cost_micros": 10432580000,
                "ctr": 7.71,
                "average_cpc": 193.20,
                "cost": 10432.58,
                "conversions": 1.00,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1003",
                "campaign_name": "Divisiones de Oficina - Search",
                "clicks": 25,
                "impressions": 329,
                "cost_micros": 3793720000,
                "ctr": 7.60,
                "average_cpc": 151.75,
                "cost": 3793.72,
                "conversions": 1.00,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1004",
                "campaign_name": "Boxes Sanitarios - Leads",
                "clicks": 4,
                "impressions": 19,
                "cost_micros": 745200000,
                "ctr": 21.05,
                "average_cpc": 186.30,
                "cost": 745.20,
                "conversions": 0.03,
            },
        ]

    def _get_mock_search_terms(self) -> list[dict[str, object]]:
        """Return sample search term rows for development mode."""

        return [
            {
                "date": "2026-03-17",
                "campaign_id": "1001",
                "campaign_name": "Tabiques Sanitarios - Búsqueda",
                "search_term": "tabiques sanitarios",
                "impressions": 180,
                "clicks": 15,
                "ctr": 8.33,
                "cost_micros": 2464800000,
                "cost": 2464.80,
                "conversions": 1,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1002",
                "campaign_name": "Divisiones para Baños - Search",
                "search_term": "divisiones para baños",
                "impressions": 125,
                "clicks": 11,
                "ctr": 8.80,
                "cost_micros": 2125200000,
                "cost": 2125.20,
                "conversions": 1,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1003",
                "campaign_name": "Divisiones de Oficina - Search",
                "search_term": "divisiones de oficina",
                "impressions": 94,
                "clicks": 8,
                "ctr": 8.51,
                "cost_micros": 1214000000,
                "cost": 1214.00,
                "conversions": 1,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1004",
                "campaign_name": "Boxes Sanitarios - Leads",
                "search_term": "boxes sanitarios",
                "impressions": 19,
                "clicks": 4,
                "ctr": 21.05,
                "cost_micros": 745200000,
                "cost": 745.20,
                "conversions": 0,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1001",
                "campaign_name": "Tabiques Sanitarios - Búsqueda",
                "search_term": "paneles sanitarios",
                "impressions": 51,
                "clicks": 7,
                "ctr": 13.73,
                "cost_micros": 1150240000,
                "cost": 1150.24,
                "conversions": 0,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1002",
                "campaign_name": "Divisiones para Baños - Search",
                "search_term": "tabiques para baños",
                "impressions": 50,
                "clicks": 2,
                "ctr": 4.00,
                "cost_micros": 386400000,
                "cost": 386.40,
                "conversions": 0,
            },
        ]

    @staticmethod
    def _normalize_enum(value: Any) -> str:
        """Return a readable enum name from proto-plus values."""

        enum_name = getattr(value, "name", None)
        if isinstance(enum_name, str) and enum_name:
            return enum_name

        return str(value)

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        """Return a float value with a safe default."""

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _micros_to_currency(self, value: Any) -> float:
        """Convert Google Ads micros values to standard currency units."""

        return self._to_float(value) / 1_000_000

    def _search(self, query: str):
        """Execute a Google Ads search query with shared safeguards."""

        if self.client is None:
            raise GoogleAdsServiceError(
                "Google Ads client is not available. Check credentials and initialization settings."
            )

        google_ads_service = self.client.get_service("GoogleAdsService")
        return google_ads_service.search(
            customer_id=self.settings.google_ads_customer_id,
            query=query,
        )

    def get_campaigns(self) -> list[dict[str, object]]:
        """Return normalized campaign data from Google Ads or mock fixtures."""

        if self.mock_mode:
            self.logger.debug("Returning mock campaign data.")
            return self._get_mock_campaigns()

        if self.client is None:
            raise GoogleAdsServiceError(
                "Google Ads client is not available. Check credentials and initialization settings."
            )

        # TODO: Expand the GAQL query only when campaign filtering or account-specific fields are required.
        try:
            google_ads_service = self.client.get_service("GoogleAdsService")
            response = google_ads_service.search(
                customer_id=self.settings.google_ads_customer_id,
                query=GAQL_CAMPAIGNS_QUERY,
            )

            campaigns: list[dict[str, object]] = []
            for row in response:
                campaigns.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "status": self._normalize_enum(row.campaign.status),
                        "advertising_channel_type": self._normalize_enum(
                            row.campaign.advertising_channel_type
                        ),
                    }
                )

            return campaigns
        except GoogleAdsException as exc:
            self.logger.exception("Google Ads campaign fetch failed.")
            raise GoogleAdsServiceError(
                "Failed to fetch campaigns from Google Ads. Check account access and customer ID configuration."
            ) from exc
        except Exception as exc:
            self.logger.exception("Unexpected error while fetching campaigns.")
            raise GoogleAdsServiceError(
                "Unable to fetch campaigns from Google Ads. Review service configuration and try again."
            ) from exc

    def get_campaign_metrics(self, date_from: str, date_to: str) -> list[dict[str, object]]:
        """Return campaign metrics rows or a clear placeholder in real mode."""

        if self.mock_mode:
            self.logger.debug(
                "Returning mock campaign metrics for date range %s to %s.",
                date_from,
                date_to,
            )
            return self._get_mock_campaign_metrics()

        query = GAQL_CAMPAIGN_METRICS_QUERY.format(
            date_from=date_from,
            date_to=date_to,
        )

        try:
            response = self._search(query)
            campaign_metrics: list[dict[str, object]] = []

            for row in response:
                cost_micros = int(self._to_float(row.metrics.cost_micros))
                average_cpc_micros = self._to_float(row.metrics.average_cpc)

                campaign_metrics.append(
                    {
                        "date": str(row.segments.date),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "impressions": int(self._to_float(row.metrics.impressions)),
                        "clicks": int(self._to_float(row.metrics.clicks)),
                        "cost_micros": cost_micros,
                        "cost": self._micros_to_currency(cost_micros),
                        "ctr": self._to_float(row.metrics.ctr),
                        "average_cpc": self._micros_to_currency(average_cpc_micros),
                        "conversions": self._to_float(row.metrics.conversions),
                    }
                )

            return campaign_metrics
        except GoogleAdsException as exc:
            self.logger.exception("Google Ads campaign metrics fetch failed.")
            raise GoogleAdsServiceError(
                "Failed to fetch campaign metrics from Google Ads. Check account access and date range."
            ) from exc
        except Exception as exc:
            self.logger.exception("Unexpected error while fetching campaign metrics.")
            raise GoogleAdsServiceError(
                "Unable to fetch campaign metrics from Google Ads. Review service configuration and try again."
            ) from exc

    def get_search_terms(self, date_from: str, date_to: str) -> list[dict[str, object]]:
        """Return search term rows or a clear placeholder in real mode."""

        if self.mock_mode:
            self.logger.debug(
                "Returning mock search terms for date range %s to %s.",
                date_from,
                date_to,
            )
            return self._get_mock_search_terms()

        query = GAQL_SEARCH_TERMS_QUERY.format(
            date_from=date_from,
            date_to=date_to,
        )

        try:
            response = self._search(query)
            search_terms: list[dict[str, object]] = []

            for row in response:
                cost_micros = int(self._to_float(row.metrics.cost_micros))

                search_terms.append(
                    {
                        "date": str(row.segments.date),
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "search_term": row.search_term_view.search_term,
                        "impressions": int(self._to_float(row.metrics.impressions)),
                        "clicks": int(self._to_float(row.metrics.clicks)),
                        "ctr": self._to_float(row.metrics.ctr),
                        "cost_micros": cost_micros,
                        "cost": self._micros_to_currency(cost_micros),
                        "conversions": self._to_float(row.metrics.conversions),
                    }
                )

            return search_terms
        except GoogleAdsException as exc:
            self.logger.exception("Google Ads search terms fetch failed.")
            raise GoogleAdsServiceError(
                "Failed to fetch search terms from Google Ads. Check account access and date range."
            ) from exc
        except Exception as exc:
            self.logger.exception("Unexpected error while fetching search terms.")
            raise GoogleAdsServiceError(
                "Unable to fetch search terms from Google Ads. Review service configuration and try again."
            ) from exc