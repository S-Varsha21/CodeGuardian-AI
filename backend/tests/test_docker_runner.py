
import subprocess
from unittest.mock import patch

from backend.app.docker_runner import run_python_code


def test_docker_runner_executes_code_successfully():
    execution_result = subprocess.CompletedProcess(
        args=["docker", "run"],
        returncode=0,
        stdout="30\n",
        stderr="",
    )

    cleanup_result = subprocess.CompletedProcess(
        args=["docker", "rm"],
        returncode=0,
        stdout="",
        stderr="",
    )

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            side_effect=[execution_result, cleanup_result],
        ) as mock_run,
    ):
        result = run_python_code("print(10 + 20)")

    assert result["status"] == "completed"
    assert result["stdout"] == "30\n"
    assert result["stderr"] == ""
    assert result["exit_code"] == 0
    assert "cleanup_warning" not in result
    assert mock_run.call_count == 2


def test_docker_runner_handles_timeout():
    cleanup_result = subprocess.CompletedProcess(
        args=["docker", "rm"],
        returncode=0,
        stdout="",
        stderr="",
    )

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            side_effect=[
                subprocess.TimeoutExpired(
                    cmd="docker run",
                    timeout=5,
                ),
                cleanup_result,
            ],
        ),
    ):
        result = run_python_code("import time; time.sleep(10)")

    assert result["status"] == "timeout"
    assert result["exit_code"] is None
    assert result["stderr"] == "Execution exceeded the time limit."


def test_docker_runner_handles_missing_docker():
    with patch(
        "backend.app.docker_runner.shutil.which",
        return_value=None,
    ):
        result = run_python_code("print('Hello')")

    assert result["status"] == "error"
    assert result["stderr"] == "Docker executable was not found."


def test_docker_runner_handles_execution_error():
    cleanup_result = subprocess.CompletedProcess(
        args=["docker", "rm"],
        returncode=0,
        stdout="",
        stderr="",
    )

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            side_effect=[
                OSError("Docker unavailable"),
                cleanup_result,
            ],
        ),
    ):
        result = run_python_code("print('Hello')")

    assert result["status"] == "error"
    assert result["stderr"] == "Docker could not be started."


def test_docker_runner_reports_cleanup_failure():
    execution_result = subprocess.CompletedProcess(
        args=["docker", "run"],
        returncode=0,
        stdout="Hello\n",
        stderr="",
    )

    cleanup_result = subprocess.CompletedProcess(
        args=["docker", "rm"],
        returncode=1,
        stdout="",
        stderr="Cleanup failed",
    )

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            side_effect=[execution_result, cleanup_result],
        ),
    ):
        result = run_python_code("print('Hello')")

    assert result["status"] == "completed"
    assert result["cleanup_warning"] == (
        "Container cleanup could not be confirmed."
    )
