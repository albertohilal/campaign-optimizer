"""Report generator service tests."""

from app.services.report_generator import ReportGeneratorService


def test_report_generator_consolidates_analysis_payload() -> None:
    """The report generator should include snapshot, findings, recommendations, and simulation."""

    service = ReportGeneratorService()

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
                "campaign_id": "1001",
                "campaign_name": "Search Alpha",
                "clicks": 34,
                "average_cpc": 220.0,
                "cost": 2500.0,
                "conversions": 0,
                "ctr": 2.8,
            }
        ],
        "search_terms": [],
    }
    findings_payload = {
        "summary": {
            "campaign_count": 1,
            "metric_rows": 1,
            "search_term_rows": 0,
        },
        "findings": [
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
            }
        ],
    }

    result = service.generate_report(
        snapshot=snapshot,
        findings_payload=findings_payload,
    )

    assert result["report_type"] == "analysis_report"
    assert result["execution_mode"] == "dry_run"
    assert result["summary"]["campaign_count"] == 1
    assert result["summary"]["finding_count"] == 1
    assert result["recommendations"]
    assert result["simulation"]["prioritized_actions"]
    assert result["snapshot_summary"]["campaign_metric_rows"] == 1
