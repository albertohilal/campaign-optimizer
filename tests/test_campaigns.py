"""Campaign endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_campaigns_returns_mock_data() -> None:
    """Ensure the campaigns endpoint returns mock campaign data in development mode."""

    client = TestClient(app)

    response = client.get("/campaigns")

    assert response.status_code == 200

    payload = response.json()

    assert isinstance(payload, list)
    assert len(payload) > 0

    first_campaign = payload[0]

    assert "campaign_id" in first_campaign
    assert "campaign_name" in first_campaign
    assert "status" in first_campaign
    assert "advertising_channel_type" in first_campaign