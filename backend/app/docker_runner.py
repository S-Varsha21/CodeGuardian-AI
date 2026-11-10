
import shutil
import subprocess
import uuid

DOCKER_IMAGE = "codeguardian-runner:dev"
EXECUTION_TIMEOUT = 5
CLEANUP_TIMEOUT = 10


def run_python_code(code: str) -> dict:
    """Execute trusted Python code in a restricted Docker container."""

    docker_path = shutil.which("docker")

    if docker_path is None:
        return {
            "status": "error",
            "stdout": "",
            "stderr": "Docker executable was not found.",
            "exit_code": None,
        }

    container_name = f"codeguardian-{uuid.uuid4().hex}"

    command = [
        docker_path,
        "run",
        "--name",
        container_name,
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "128m",
        "--cpus",
        "0.5",
        DOCKER_IMAGE,
        "-c",
        code,
    ]

    output = {
        "status": "error",
        "stdout": "",
        "stderr": "",
        "exit_code": None,
    }

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT,
            check=False,
        )

        output = {
            "status": "completed",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        output["status"] = "timeout"
        output["stderr"] = "Execution exceeded the time limit."

    except OSError:
        output["stderr"] = "Docker could not be started."

    finally:
        try:
            cleanup = subprocess.run(
                [docker_path, "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=CLEANUP_TIMEOUT,
                check=False,
            )

            if cleanup.returncode != 0:
                output["cleanup_warning"] = (
                    "Container cleanup could not be confirmed."
                )

        except (OSError, subprocess.TimeoutExpired):
            output["cleanup_warning"] = (
                "Container cleanup could not be confirmed."
            )

    return output
