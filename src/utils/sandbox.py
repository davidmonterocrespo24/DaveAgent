"""
Docker sandbox utilities for DaveAgent.

When Docker is available, DaveAgent relaunches itself inside a container with
the user's project mounted as a volume. Inside the container, DAVEAGENT_SANDBOX=1
is set, which causes all tool approvals to be auto-approved.
"""

import os
import subprocess
import sys
from pathlib import Path


def is_inside_sandbox() -> bool:
    """True when DAVEAGENT_SANDBOX env var is '1' (we are already inside Docker)."""
    return os.environ.get("DAVEAGENT_SANDBOX") == "1"


def is_docker_available() -> bool:
    """Runs `docker info` to check if Docker daemon is reachable. Returns False on any error."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def get_container_path(host_path: str) -> str:
    """Converts a host path to a Docker-compatible path.

    On Windows: E:\\AI\\project -> /e/AI/project
    Other platforms: returned as-is.
    """
    if sys.platform == "win32" and len(host_path) >= 2 and host_path[1] == ":":
        drive = host_path[0].lower()
        rest = host_path[2:].replace("\\", "/")
        return f"/{drive}{rest}"
    return host_path


def get_daveagent_root() -> Path:
    """Returns the daveagent package root directory."""
    return Path(__file__).resolve().parent.parent.parent


def image_exists(image_name: str) -> bool:
    """Returns True if the named Docker image exists locally."""
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def build_image(image_name: str) -> bool:
    """Builds the sandbox Docker image, streaming output to stdout.

    Returns True on success, False on failure.
    """
    daveagent_root = get_daveagent_root()
    dockerfile = daveagent_root / "Dockerfile.sandbox"

    print(f"[INFO] Building Docker sandbox image '{image_name}'...")
    print(f"[INFO] Build context: {daveagent_root}")

    try:
        result = subprocess.run(
            [
                "docker", "build",
                "-t", image_name,
                "-f", str(dockerfile),
                str(daveagent_root),
            ],
            # No capture — stream directly to user's terminal
        )
        return result.returncode == 0
    except (FileNotFoundError, OSError) as e:
        print(f"[ERROR] Docker build failed: {e}")
        return False


def ensure_image(image_name: str) -> bool:
    """Ensures the sandbox image exists, building it if necessary.

    Returns False if the image could not be built.
    """
    if image_exists(image_name):
        return True
    return build_image(image_name)


def collect_env_vars() -> list:
    """Returns a flat list of ['-e', 'KEY=VAL', ...] for docker run.

    Forwards known DaveAgent env vars if set, and always sets DAVEAGENT_SANDBOX=1.
    """
    forwarded = [
        "DAVEAGENT_API_KEY",
        "DAVEAGENT_BASE_URL",
        "DAVEAGENT_MODEL",
        "DAVEAGENT_BASE_MODEL",
        "DAVEAGENT_STRONG_MODEL",
        "DAVEAGENT_SSL_VERIFY",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
    ]

    env_args = []
    for key in forwarded:
        val = os.environ.get(key)
        if val is not None:
            env_args.extend(["-e", f"{key}={val}"])

    # Always mark as inside sandbox
    env_args.extend(["-e", "DAVEAGENT_SANDBOX=1"])

    return env_args


def start_sandbox(cli_args: list) -> int:
    """Relaunches the current process inside a Docker sandbox container.

    Returns the container exit code, or -1 if the sandbox could not be started
    (caller should fall back to running normally with approval prompts).
    """
    image_name = os.environ.get("DAVEAGENT_SANDBOX_IMAGE", "daveagent-sandbox:latest")

    if not ensure_image(image_name):
        return -1

    workdir_host = os.getcwd()
    workdir_container = get_container_path(workdir_host)

    pkg_host = str(get_daveagent_root())
    pkg_container = get_container_path(pkg_host)

    env_args = collect_env_vars()
    tty_flag = ["-t"] if sys.stdin.isatty() else []

    cmd = (
        ["docker", "run", "--rm", "-i"]
        + tty_flag
        + [
            "--init",
            "--workdir", workdir_container,
            "-v", f"{workdir_host}:{workdir_container}",
            "-v", f"{pkg_host}:{pkg_container}",
        ]
        + env_args
        + [image_name, "daveagent"]
        + cli_args
    )

    print("[INFO] Starting DaveAgent in Docker sandbox...")

    if sys.platform == "win32":
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    else:
        os.execvp("docker", cmd)

    # Unreachable, but satisfies type checkers
    return 0
