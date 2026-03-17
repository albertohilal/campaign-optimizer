"""Simulation service tests."""

from app.services.simulation_service import SimulationService


def test_simulation_builds_ui_payload_from_analyzer_findings() -> None:
    """The simulation payload should be readable and grouped by campaign."""
    service = SimulationService()

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

    result = service.simulate(findings=findings)

    assert result["simulation"] is True
    assert result["execution_mode"] == "dry_run"
    assert result["summary"]["campaign_count"] == 1
    assert result["summary"]["finding_count"] == 2
    assert len(result["prioritized_actions"]) >= 2
    assert result["campaigns"][0]["campaign_name"] == "Search Alpha"
    assert "Highest priority" in result["campaigns"][0]["summary_text"]
    assert result["prioritized_actions"][0]["explanation"]


def test_simulation_accepts_actions_without_findings() -> None:
    """Direct actions should still produce a usable simulation response."""
    service = SimulationService()

    actions = [
        {
            "action_type": "increase_budget",
            "entity": "campaign",
            "entity_id": "1002",
            "campaign_id": "1002",
            "priority": 78,
            "reason": "Budget limitation detected.",
            "source_finding_type": "budget_limited",
            "params": {"percentage": 15, "campaign_name": "Search Beta"},
            "requires_review": True,
        }
    ]

    result = service.simulate(actions=actions)

    assert result["summary"]["finding_count"] == 0
    assert result["summary"]["provided_action_count"] == 1
    assert result["summary"]["final_action_count"] == 1
    assert result["campaigns"][0]["campaign_name"] == "Search Beta"
    assert result["prioritized_actions"][0]["action_label"] == "Increase budget 15%"
    assert result["prioritized_actions"][0]["simulation_only"] is True


def test_simulation_groups_campaigns_by_name_when_campaign_id_is_missing() -> None:
    """Findings with campaign_name only should still be grouped correctly."""
    service = SimulationService()

    findings = [
        {
            "code": "low_ctr",
            "severity": "medium",
            "message": "CTR is below expected threshold.",
            "metadata": {
                "campaign_name": "Search Gamma",
                "ctr": 1.9,
            },
        }
    ]

    result = service.simulate(findings=findings)

    assert result["summary"]["campaign_count"] == 1
    assert result["campaigns"][0]["campaign_name"] == "Search Gamma"
    assert result["campaigns"][0]["finding_count"] == 1
    assert result["campaigns"][0]["action_count"] >= 1


def test_simulation_maps_high_average_cpc_without_forcing_pause_logic() -> None:
    """High average CPC should map to a softer action than pause-by-default."""
    service = SimulationService()

    findings = [
        {
            "code": "high_average_cpc",
            "severity": "high",
            "message": "Average CPC is above threshold.",
            "metadata": {
                "campaign_id": "1003",
                "campaign_name": "Search Delta",
                "average_cpc": 950.0,
                "clicks": 8,
                "conversions": 1,
            },
        }
    ]

    result = service.simulate(findings=findings)

    assert result["summary"]["campaign_count"] == 1
    assert len(result["prioritized_actions"]) >= 1
    assert result["prioritized_actions"][0]["action_type"] in {
        "decrease_bid",
        "flag_for_manual_review",
    }