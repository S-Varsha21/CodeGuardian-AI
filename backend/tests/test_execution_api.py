
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_execution_disabled_by_default():
    with (
        patch.dict(
            "os.environ",
            {"CODEGUARDIAN_ENABLE_EXECUTION": "false"},
        ),
        patch(
            "backend.app.main.run_python_code",
        ) as mock_runner,
    ):
        response = client.post(
            "/execute",
            json={"code": "print(30)"},
        )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Code execution is disabled."
    }
    mock_runner.assert_not_called()


def test_execution_enabled_for_trusted_development():
    expected_result = {
        "status": "completed",
        "stdout": "30\n",
        "stderr": "",
        "exit_code": 0,
    }

    with (
        patch.dict(
            "os.environ",
            {"CODEGUARDIAN_ENABLE_EXECUTION": "true"},
        ),
        patch(
            "backend.app.main.run_python_code",
            return_value=expected_result,
        ) as mock_runner,
    ):
        response = client.post(
            "/execute",
            json={"code": "print(30)"},
        )

    assert response.status_code == 200
    assert response.json() == expected_result
    mock_runner.assert_called_once_with("print(30)")


def test_execution_rejects_oversized_code():
    with (
        patch.dict(
            "os.environ",
            {"CODEGUARDIAN_ENABLE_EXECUTION": "true"},
        ),
        patch(
            "backend.app.main.run_python_code",
        ) as mock_runner,
    ):
        response = client.post(
            "/execute",
            json={"code": "a" * 10_001},
        )

    assert response.status_code == 422
    mock_runner.assert_not_called()

