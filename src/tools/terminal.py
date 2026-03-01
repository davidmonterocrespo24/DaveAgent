"""
Tool for executing terminal commands safely
"""

import asyncio

from src.tools.common import get_workspace

# Global reference to orchestrator (for real-time output streaming)
_orchestrator = None


def set_orchestrator(orchestrator):
    """Initialize the terminal tool with orchestrator instance."""
    global _orchestrator
    _orchestrator = orchestrator


async def run_terminal_cmd(
    command: str,
    is_background: bool = False,
    require_user_approval: bool = False,
    explanation: str = "",
) -> str:
    """Executes a terminal command using async subprocess (non-blocking)"""
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
        import logging

        from src.utils.interaction import ask_for_approval

        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️  Command requires approval: {command}")

        explanation_text = f"Command: {command}\n{explanation}"
        approval_result = await ask_for_approval(
            action_description="COMMAND APPROVAL REQUIRED", context=f"```bash\n{command}\n```"
        )

        if approval_result:
            logger.info(f"❌ Command denied or feedback provided: {approval_result}")
            if _orchestrator:
                _orchestrator.cli.print_error(f"Command cancelled: {approval_result}")
            return approval_result
        else:
            logger.info(f"✅ Command approved by user: {command}")
            if _orchestrator:
                _orchestrator.cli.print_success("✅ Command approved, executing...")

    try:
        workspace = get_workspace()

        # CRITICAL FIX: Use async subprocess to avoid blocking event loop
        # This allows the spinner to continue rotating during long commands
        # CRITICAL: Set stdin=DEVNULL to prevent interactive commands (like unzip) from hanging forever
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workspace),
        )

        # Stream output line-by-line for real-time feedback
        stdout_lines = []
        stderr_lines = []

        async def read_stream(stream, lines_list):
            """Read stream line-by-line and print in real-time."""
            while True:
                line = await stream.readline()
                if not line:
                    break
                line_text = line.decode("utf-8", errors="replace").rstrip()
                lines_list.append(line_text)
                # Print to terminal in real-time using CLI (cleaner than print())
                if line_text.strip() and _orchestrator is not None:
                    _orchestrator.cli.print_thinking(f"  {line_text}")

        try:
            # Read both streams concurrently with timeout
            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(process.stdout, stdout_lines),
                    read_stream(process.stderr, stderr_lines),
                ),
                timeout=60,
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except TimeoutError:
                process.kill()
                await process.wait()
        except TimeoutError:
            process.kill()
            return "Error: Command timed out after 60 seconds"

        # Build output from accumulated lines
        output_parts = [f"Command: {command}", f"Exit code: {process.returncode}\n"]

        if stdout_lines:
            stdout_text = "\n".join(stdout_lines)
            if stdout_text.strip():
                output_parts.append(f"STDOUT:\n{stdout_text}")

        if stderr_lines:
            stderr_text = "\n".join(stderr_lines)
            if stderr_text.strip():
                output_parts.append(f"STDERR:\n{stderr_text}")

        result = "\n".join(output_parts) if output_parts else "(no output)"

        # Truncate very long output to avoid context saturation
        max_len = 10000
        if len(result) > max_len:
            result = result[:max_len] + f"\n... (truncated, {len(result) - max_len} more chars)"

        return result

    except Exception as e:
        return f"Error executing command: {str(e)}"
