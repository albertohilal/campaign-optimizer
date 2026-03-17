"""Google Ads client normalization tests."""

from __future__ import annotations

from logging import getLogger
from types import SimpleNamespace

from app.services.google_ads_client import GoogleAdsClientService


class _FakeGoogleAdsService:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows
        self.last_query = ""
        self.last_customer_id = ""

    def search(self, customer_id: str, query: str):
        self.last_customer_id = customer_id
        self.last_query = query
        return self.rows


class _FakeClient:
    def __init__(self, rows: list[object]) -> None:
        self.service = _FakeGoogleAdsService(rows)

    def get_service(self, _: str) -> _FakeGoogleAdsService:
        return self.service


def _build_service(rows: list[object]) -> tuple[GoogleAdsClientService, _FakeGoogleAdsService]:
    service = GoogleAdsClientService.__new__(GoogleAdsClientService)
    service.settings = SimpleNamespace(google_ads_customer_id="1234567890")
    service.logger = getLogger("test-google-ads-client")
    service.mock_mode = False
    service.client = _FakeClient(rows)
    return service, service.client.service


def test_get_campaign_metrics_normalizes_real_google_ads_rows() -> None:
    """Campaign metrics should preserve required fields and normalize micros."""

    rows = [
        SimpleNamespace(
            segments=SimpleNamespace(date="2026-03-17"),
            campaign=SimpleNamespace(id=1001, name="Search Alpha"),
            metrics=SimpleNamespace(
                impressions=753,
                clicks=50,
                cost_micros=8215880000,
                ctr=6.64,
                average_cpc=164320000,
                conversions=1.05,
            ),
        )
    ]

    service, fake_google_ads_service = _build_service(rows)

    result = service.get_campaign_metrics("2026-03-01", "2026-03-17")

    assert len(result) == 1
    assert result[0]["date"] == "2026-03-17"
    assert result[0]["campaign_id"] == "1001"
    assert result[0]["campaign_name"] == "Search Alpha"
    assert result[0]["impressions"] == 753
    assert result[0]["clicks"] == 50
    assert result[0]["cost_micros"] == 8215880000
    assert result[0]["cost"] == 8215.88
    assert result[0]["average_cpc"] == 164.32
    assert result[0]["conversions"] == 1.05
    assert "FROM campaign" in fake_google_ads_service.last_query
    assert "BETWEEN '2026-03-01' AND '2026-03-17'" in fake_google_ads_service.last_query


def test_get_search_terms_normalizes_real_google_ads_rows() -> None:
    """Search terms should preserve required fields and normalize micros."""

    rows = [
        SimpleNamespace(
            segments=SimpleNamespace(date="2026-03-17"),
            campaign=SimpleNamespace(id=1001, name="Search Alpha"),
            search_term_view=SimpleNamespace(search_term="tabiques sanitarios"),
            metrics=SimpleNamespace(
                impressions=180,
                clicks=15,
                ctr=8.33,
                cost_micros=2464800000,
                conversions=1.0,
            ),
        )
    ]

    service, fake_google_ads_service = _build_service(rows)

    result = service.get_search_terms("2026-03-01", "2026-03-17")

    assert len(result) == 1
    assert result[0]["date"] == "2026-03-17"
    assert result[0]["campaign_id"] == "1001"
    assert result[0]["campaign_name"] == "Search Alpha"
    assert result[0]["search_term"] == "tabiques sanitarios"
    assert result[0]["impressions"] == 180
    assert result[0]["clicks"] == 15
    assert result[0]["ctr"] == 8.33
    assert result[0]["cost_micros"] == 2464800000
    assert result[0]["cost"] == 2464.8
    assert result[0]["conversions"] == 1.0
    assert "FROM search_term_view" in fake_google_ads_service.last_query
    assert "BETWEEN '2026-03-01' AND '2026-03-17'" in fake_google_ads_service.last_query