
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_homepage_returns_welcome_message():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to CodeGuardian AI",
        "status": "running",
    }


def test_health_endpoint_reports_healthy():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "CodeGuardian AI",
    }
