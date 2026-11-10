
import subprocess
from unittest.mock import patch

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


def test_analyze_accepts_valid_python_code():
    response = client.post(
        "/analyze",
        json={"code": "def add(a, b):\n    return a + b"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["syntax_valid"] is True
    assert data["syntax_error"] is None
    assert data["line_count"] == 2


def test_analyze_detects_invalid_python_code():
    response = client.post(
        "/analyze",
        json={"code": "def add(a, b)\n    return a + b"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["syntax_valid"] is False
    assert data["syntax_error"] is not None
    assert data["line_count"] == 2


def test_analyze_handles_empty_code():
    response = client.post(
        "/analyze",
        json={"code": ""},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["syntax_valid"] is True
    assert data["syntax_error"] is None
    assert data["line_count"] == 0


def test_analyze_detects_unsafe_eval():
    response = client.post(
        "/analyze",
        json={
            "code": (
                "user_input = input('Enter expression: ')\n"
                "result = eval(user_input)\n"
                "print(result)"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["syntax_valid"] is True
    assert data["security_scan_error"] is None
    assert any(
        finding["test_id"] == "B307"
        for finding in data["security_findings"]
    )


def test_analyze_handles_security_scan_timeout():
    with patch(
        "backend.app.main.scan_security_issues",
        side_effect=subprocess.TimeoutExpired(
            cmd="bandit",
            timeout=10,
        ),
    ):
        response = client.post(
            "/analyze",
            json={"code": "print('Hello World')"},
        )

    assert response.status_code == 200

    data = response.json()
    assert data["syntax_valid"] is True
    assert data["security_findings"] == []
    assert data["security_scan_error"] == "Security scan timed out."


def test_analyze_rejects_oversized_code():
    response = client.post(
        "/analyze",
        json={"code": "a" * 100_001},
    )

    assert response.status_code == 422
