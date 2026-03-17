"""Campaign report endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_campaign_report_returns_consolidated_dry_run_payload() -> None:
    """The campaign report route should orchestrate the existing analysis flow."""

    client = TestClient(app)

    response = client.get(
        "/campaigns/1001/report",
        params={"date_from": "2026-03-01", "date_to": "2026-03-17"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["campaign_id"] == "1001"
    assert payload["report_type"] == "analysis_report"
    assert payload["execution_mode"] == "dry_run"
    assert payload["summary"]["campaign_count"] == 1
    assert payload["campaigns"][0]["campaign_id"] == "1001"
    assert payload["simulation"]["prioritized_actions"]
    assert payload["recommendations"]


def test_campaign_report_returns_not_found_for_unknown_campaign() -> None:
    """Unknown campaigns should return a controlled 404 response."""

    client = TestClient(app)

    response = client.get(
        "/campaigns/9999/report",
        params={"date_from": "2026-03-01", "date_to": "2026-03-17"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Campaign '9999' was not found for the requested report scope."
    )