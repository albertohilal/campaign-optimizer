"""Recommendations service tests."""

from app.services.recommendations import RecommendationsService


def test_recommendations_service_builds_dry_run_payload() -> None:
    """Recommendations should be readable and derived from findings."""

    service = RecommendationsService()

    findings = [
        {
            "code": "spend_without_conversions",
            "severity": "high",
            "message": "Campaign spent budget without conversions.",
            "metadata": {
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "cost": 2500.0,
                "conversions": 0,
                "clicks": 34,
            },
        },
        {
            "code": "low_ctr",
            "severity": "medium",
            "message": "CTR is below expected threshold.",
            "metadata": {
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "ctr": 2.8,
            },
        },
    ]

    result = service.build_recommendations(findings=findings)

    assert result["dry_run"] is True
    assert result["summary"]["finding_count"] == 2
    assert result["summary"]["campaign_count"] == 1
    assert result["summary"]["recommendation_count"] >= 2
    assert result["campaigns"][0]["campaign_name"] == "Search Alpha"
    assert result["recommendations"][0]["title"]
    assert result["recommendations"][0]["detail"]
