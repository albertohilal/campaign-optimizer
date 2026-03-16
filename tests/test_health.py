"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    """Ensure the health endpoint responds successfully."""

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"