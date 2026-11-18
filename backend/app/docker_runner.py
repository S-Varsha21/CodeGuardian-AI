
import selectors
import shutil
import subprocess
import time
import uuid

DOCKER_IMAGE = "codeguardian-runner:dev"
EXECUTION_TIMEOUT = 5
CLEANUP_TIMEOUT = 10
MAX_OUTPUT_BYTES = 10_000


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

    process = None
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    deadline = time.monotonic() + EXECUTION_TIMEOUT

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")

            while selector.get_map():
                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    output["status"] = "timeout"
                    output["stderr"] = "Execution exceeded the time limit."
                    break

                events = selector.select(timeout=remaining)

                if not events:
                    output["status"] = "timeout"
                    output["stderr"] = "Execution exceeded the time limit."
                    break

                for key, _ in events:
                    chunk = key.fileobj.read(4096)

                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue

                    buffer = (
                        stdout_buffer
                        if key.data == "stdout"
                        else stderr_buffer
                    )

                    space = MAX_OUTPUT_BYTES - len(buffer)

                    if space > 0:
                        buffer.extend(chunk[:space])

        if output["status"] != "timeout":
            remaining = max(0, deadline - time.monotonic())

            try:
                exit_code = process.wait(timeout=remaining)
                output = {
                    "status": "completed",
                    "stdout": stdout_buffer.decode(
                        "utf-8", errors="replace"
                    ),
                    "stderr": stderr_buffer.decode(
                        "utf-8", errors="replace"
                    ),
                    "exit_code": exit_code,
                }
            except subprocess.TimeoutExpired:
                output["status"] = "timeout"
                output["stderr"] = "Execution exceeded the time limit."

    except OSError:
        output["stderr"] = "Docker could not be started."

    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()

            try:
                process.wait(timeout=CLEANUP_TIMEOUT)
            except subprocess.TimeoutExpired:
                output["cleanup_warning"] = (
                    "Docker process termination could not be confirmed."
                )

            if process.stdout:
                process.stdout.close()

            if process.stderr:
                process.stderr.close()

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
