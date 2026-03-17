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


def test_analysis_campaign_diagnosis_returns_executive_summary() -> None:
    """The campaign diagnosis route should return deduplicated campaign summaries."""

    client = TestClient(app)

    campaign_id = "23407773961"

    response = client.get(
        "/analysis/campaign-diagnosis",
        params={
            "date_from": "2026-03-01",
            "date_to": "2026-03-17",
            "campaign_id": campaign_id,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["dry_run"] is True
    assert payload["summary"]["campaign_count"] == 1
    assert payload["summary"]["diagnosed_campaign_id"] == campaign_id
    assert payload["campaigns"][0]["campaign_id"] == campaign_id
    assert payload["campaigns"][0]["overall_status"] in {"critical", "warning", "healthy"}
    assert isinstance(payload["campaigns"][0]["top_issues"], list)
    assert isinstance(payload["campaigns"][0]["recommended_priorities"], list)