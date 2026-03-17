"""Analysis recommendations and report route tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_analysis_recommendations_returns_dry_run_payload() -> None:
    """The recommendations route should return a readable dry-run payload."""

    client = TestClient(app)

    response = client.get(
        "/analysis/recommendations",
        params={"date_from": "2026-03-01", "date_to": "2026-03-17"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["dry_run"] is True
    assert payload["summary"]["finding_count"] >= 1
    assert payload["summary"]["recommendation_count"] >= 1
    assert payload["campaigns"]
    assert payload["recommendations"]


def test_analysis_report_returns_consolidated_payload() -> None:
    """The report route should return snapshot, findings, recommendations, and simulation."""

    client = TestClient(app)

    response = client.get(
        "/analysis/report",
        params={"date_from": "2026-03-01", "date_to": "2026-03-17"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["report_type"] == "analysis_report"
    assert payload["execution_mode"] == "dry_run"
    assert payload["summary"]["campaign_count"] >= 1
    assert payload["summary"]["finding_count"] >= 1
    assert payload["recommendations"]
    assert payload["simulation"]["prioritized_actions"]