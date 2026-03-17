"""Simulation endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_simulate_returns_payload_from_findings() -> None:
    """Ensure the simulation endpoint accepts analyzer findings and returns a dry-run payload."""

    client = TestClient(app)

    payload = {
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
    }

    response = client.post("/simulate", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert body["simulation"] is True
    assert body["execution_mode"] == "dry_run"
    assert body["summary"]["finding_count"] == 2
    assert body["summary"]["campaign_count"] == 1
    assert len(body["prioritized_actions"]) >= 1
    assert body["campaigns"][0]["campaign_name"] == "Search Alpha"


def test_simulate_returns_payload_from_actions() -> None:
    """Ensure the simulation endpoint accepts direct actions and returns a readable payload."""

    client = TestClient(app)

    payload = {
        "actions": [
            {
                "action_type": "increase_budget",
                "entity": "campaign",
                "entity_id": "1002",
                "campaign_id": "1002",
                "priority": 78,
                "reason": "Budget limitation detected.",
                "source_finding_type": "budget_limited",
                "params": {
                    "percentage": 15,
                    "campaign_name": "Search Beta",
                },
                "requires_review": True,
            }
        ]
    }

    response = client.post("/simulate", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert body["simulation"] is True
    assert body["summary"]["provided_action_count"] == 1
    assert body["summary"]["final_action_count"] == 1
    assert body["campaigns"][0]["campaign_name"] == "Search Beta"
    assert body["prioritized_actions"][0]["action_type"] == "increase_budget"
    assert body["prioritized_actions"][0]["action_label"] == "Increase budget 15%"