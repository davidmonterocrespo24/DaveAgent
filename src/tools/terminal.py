"""
Tool for executing terminal commands safely
"""
import os
import subprocess
from pathlib import Path

from src.tools.common import get_workspace


async def run_terminal_cmd(
        command: str,
        is_background: bool = False,
        require_user_approval: bool = False,
        explanation: str = ""
) -> str:
    """Executes a terminal command"""
    dangerous_keywords = [
        "rm",
        "del",
        "format",
        "shutdown",
        "reboot",
        "kill",
        "pip install",
        "npm install",
        "apt-get",
        "yum",
        "curl",
        "wget",
    ]

    is_dangerous = any(keyword in command.lower() for keyword in dangerous_keywords)

    if require_user_approval or is_dangerous:
        approval_msg = f"""
            ==================================================================
            COMMAND APPROVAL REQUIRED
            ==================================================================
            Command: {command[:50]}
            WARNING: This command requires user approval before execution
            ==================================================================
            ACTION REQUIRED: Ask the user if they want to execute this command.
            """
        return approval_msg

    try:
        workspace = get_workspace()
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60, cwd=workspace
        )

        output = f"Command: {command}\n"
        output += f"Exit code: {result.returncode}\n\n"

        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"

        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"

        return output

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after 60 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"
