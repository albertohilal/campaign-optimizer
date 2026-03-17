"""Campaign diagnosis summary service tests."""

from app.services.campaign_diagnosis import CampaignDiagnosisService


def test_campaign_diagnosis_deduplicates_findings_and_builds_summary() -> None:
    """Diagnosis should aggregate repeated findings into a concise campaign summary."""

    service = CampaignDiagnosisService()

    snapshot = {
        "date_from": "2026-03-01",
        "date_to": "2026-03-17",
        "campaigns": [
            {
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "status": "ENABLED",
            }
        ],
        "campaign_metrics": [
            {
                "date": "2026-03-16",
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "impressions": 100,
                "clicks": 4,
                "cost": 900.0,
                "average_cpc": 225.0,
                "ctr": 4.0,
                "conversions": 0,
            },
            {
                "date": "2026-03-17",
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "impressions": 150,
                "clicks": 6,
                "cost": 1200.0,
                "average_cpc": 200.0,
                "ctr": 4.0,
                "conversions": 0,
            },
        ],
        "search_terms": [],
    }
    findings_payload = {
        "summary": {"campaign_count": 1, "metric_rows": 2, "search_term_rows": 3},
        "findings": [
            {
                "code": "spend_without_conversions",
                "severity": "high",
                "message": "Campaign spent without conversions.",
                "metadata": {
                    "campaign_id": "1001",
                    "campaign_name": "Search Alpha",
                    "cost": 900.0,
                    "conversions": 0,
                },
            },
            {
                "code": "spend_without_conversions",
                "severity": "high",
                "message": "Campaign spent without conversions.",
                "metadata": {
                    "campaign_id": "1001",
                    "campaign_name": "Search Alpha",
                    "cost": 1200.0,
                    "conversions": 0,
                },
            },
            {
                "code": "low_ctr",
                "severity": "medium",
                "message": "CTR is low.",
                "metadata": {
                    "campaign_id": "1001",
                    "campaign_name": "Search Alpha",
                    "ctr": 4.0,
                },
            },
            {
                "code": "search_term_without_conversions",
                "severity": "medium",
                "message": "Search term wasted spend.",
                "metadata": {
                    "campaign_id": "1001",
                    "search_term": "cheap traffic",
                    "clicks": 8,
                    "cost": 120.0,
                    "conversions": 0,
                },
            },
            {
                "code": "search_term_without_conversions",
                "severity": "medium",
                "message": "Search term wasted spend.",
                "metadata": {
                    "campaign_id": "1001",
                    "search_term": "cheap traffic",
                    "clicks": 4,
                    "cost_micros": 80000000,
                    "conversions": 0,
                },
            },
            {
                "code": "search_term_without_conversions",
                "severity": "medium",
                "message": "Search term wasted spend.",
                "metadata": {
                    "campaign_id": "1001",
                    "search_term": "many clicks low cost",
                    "clicks": 25,
                    "cost": 40.0,
                    "conversions": 0,
                },
            },
        ],
    }
    recommendations_payload = {
        "recommendations": [
            {
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "action_type": "review_search_terms",
                "priority_score": 85,
            },
            {
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "action_type": "decrease_bid",
                "priority_score": 72,
            },
            {
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "action_type": "review_search_terms",
                "priority_score": 60,
            },
        ]
    }

    result = service.build_campaign_diagnosis(
        snapshot=snapshot,
        findings_payload=findings_payload,
        recommendations_payload=recommendations_payload,
    )

    assert result["dry_run"] is True
    assert result["summary"]["campaign_count"] == 1
    campaign = result["campaigns"][0]
    assert campaign["campaign_id"] == "1001"
    assert campaign["campaign_name"] == "Search Alpha"
    assert campaign["overall_status"] == "critical"
    assert campaign["total_cost"] == 2100.0
    assert campaign["total_conversions"] == 0.0
    assert campaign["average_ctr"] == 4.0
    assert campaign["average_cpc"] == 210.0
    assert campaign["top_issues"][0]["code"] == "spend_without_conversions"
    assert campaign["top_issues"][0]["count"] == 2
    assert campaign["top_waste_search_terms"][0]["search_term"] == "cheap traffic"
    assert campaign["top_waste_search_terms"][0]["cost"] == 200.0
    assert campaign["top_waste_search_terms"][1]["search_term"] == "many clicks low cost"
    assert campaign["recommended_priorities"] == ["review_search_terms", "decrease_bid"]


def test_campaign_diagnosis_uses_clicks_when_cost_is_missing() -> None:
    """Waste ranking should fall back to clicks when no cost fields are available."""

    service = CampaignDiagnosisService()

    result = service._build_top_waste_search_terms(
        [
            {
                "code": "search_term_without_conversions",
                "metadata": {"search_term": "term a", "clicks": 3},
            },
            {
                "code": "search_term_without_conversions",
                "metadata": {"search_term": "term b", "clicks": 9},
            },
        ]
    )

    assert result[0]["search_term"] == "term b"
    assert result[0]["cost"] == 9.0