
import subprocess
from unittest.mock import MagicMock, patch

from backend.app.docker_runner import run_python_code


def make_process(returncode=0, stdout=b"", stderr=b""):
    """Create a mocked Docker process with readable output streams."""
    process = MagicMock()
    process.poll.return_value = returncode
    process.wait.return_value = returncode

    return process



def make_selector(stdout=b"", stderr=b""):
    """Simulate readable streams followed by end-of-file."""
    selector = MagicMock()
    selector.__enter__.return_value = selector

    stdout_stream = MagicMock()
    stderr_stream = MagicMock()

    stdout_stream.read.side_effect = [stdout, b""]
    stderr_stream.read.side_effect = [stderr, b""]

    stdout_key = MagicMock()
    stdout_key.fileobj = stdout_stream
    stdout_key.data = "stdout"

    stderr_key = MagicMock()
    stderr_key.fileobj = stderr_stream
    stderr_key.data = "stderr"

    selector.get_map.side_effect = [
        {"stdout": True, "stderr": True},
        {"stdout": True, "stderr": True},
        {},
    ]

    selector.select.side_effect = [
        [(stdout_key, 1), (stderr_key, 1)],
        [(stdout_key, 1), (stderr_key, 1)],
    ]

    return selector

def test_missing_docker():
    with patch(
        "backend.app.docker_runner.shutil.which",
        return_value=None,
    ):
        result = run_python_code("print(30)")

    assert result["status"] == "error"
    assert "Docker" in result["stderr"]


def test_docker_starts_successfully():
    process = make_process()

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.Popen",
            return_value=process,
        ),
        patch(
            "backend.app.docker_runner.selectors.DefaultSelector",
            return_value=make_selector(),
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["docker", "rm"],
                returncode=0,
            ),
        ),
    ):
        result = run_python_code("print(30)")

    assert result["status"] == "completed"
    assert result["exit_code"] == 0


def test_output_limit_constant():
    from backend.app.docker_runner import MAX_OUTPUT_BYTES

    assert MAX_OUTPUT_BYTES == 10_000


def test_docker_cleanup_warning():
    process = make_process()

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.Popen",
            return_value=process,
        ),
        patch(
            "backend.app.docker_runner.selectors.DefaultSelector",
            return_value=make_selector(),
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["docker", "rm"],
                returncode=1,
            ),
        ),
    ):
        result = run_python_code("print(30)")

    assert "cleanup_warning" in result


def test_docker_start_failure():
    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.Popen",
            side_effect=OSError("Docker failed"),
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["docker", "rm"],
                returncode=0,
            ),
        ),
    ):
        result = run_python_code("print(30)")

    assert result["status"] == "error"
    assert "Docker could not be started" in result["stderr"]


def test_execution_timeout():
    process = make_process()
    process.wait.side_effect = subprocess.TimeoutExpired(
        cmd="docker run",
        timeout=5,
    )

    selector = MagicMock()
    selector.__enter__.return_value = selector
    selector.get_map.return_value = {"stdout": True}
    selector.select.return_value = []

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.Popen",
            return_value=process,
        ),
        patch(
            "backend.app.docker_runner.selectors.DefaultSelector",
            return_value=selector,
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["docker", "rm"],
                returncode=0,
            ),
        ),
    ):
        result = run_python_code("while True: pass")

    assert result["status"] == "timeout"
    assert "time limit" in result["stderr"]


def test_output_is_bounded():
    from backend.app.docker_runner import MAX_OUTPUT_BYTES

    assert MAX_OUTPUT_BYTES == 10_000



def test_runner_truncates_large_stdout():
    """Verify that actual captured output is limited to 10,000 bytes."""
    from backend.app.docker_runner import MAX_OUTPUT_BYTES

    process = make_process()

    large_output = b"A" * 100_000
    selector = make_selector(stdout=large_output)

    with (
        patch(
            "backend.app.docker_runner.shutil.which",
            return_value="/usr/local/bin/docker",
        ),
        patch(
            "backend.app.docker_runner.subprocess.Popen",
            return_value=process,
        ),
        patch(
            "backend.app.docker_runner.selectors.DefaultSelector",
            return_value=selector,
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["docker", "rm"],
                returncode=0,
            ),
        ),
    ):
        result = run_python_code("print('A' * 100000)")

    assert result["status"] == "completed"
    assert len(result["stdout"].encode("utf-8")) == MAX_OUTPUT_BYTES
    assert result["stdout"] == "A" * MAX_OUTPUT_BYTES
    assert result["exit_code"] == 0



def test_timeout_kills_process_and_cleans_container():
    """Verify timeout triggers process termination and Docker cleanup."""
    process = make_process()
    process.poll.return_value = None

    selector = MagicMock()
    selector.__enter__.return_value = selector
    selector.get_map.return_value = {"stdout": True}
    selector.select.return_value = []

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
            "backend.app.docker_runner.subprocess.Popen",
            return_value=process,
        ),
        patch(
            "backend.app.docker_runner.selectors.DefaultSelector",
            return_value=selector,
        ),
        patch(
            "backend.app.docker_runner.subprocess.run",
            return_value=cleanup_result,
        ) as cleanup_mock,
    ):
        result = run_python_code("while True: pass")

    assert result["status"] == "timeout"
    process.kill.assert_called_once()
    cleanup_mock.assert_called_once()
    assert cleanup_mock.call_args.args[0][1:3] == ["rm", "-f"]



