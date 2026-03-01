"""
Tool for checking pending subagent announcements.

This tool allows the main agent to retrieve results from completed subagents.
It implements the Nanobot-style announcement system where subagent results
are queued and the main agent processes them naturally.
"""

# Global reference to orchestrator (injected during initialization)
_orchestrator = None


def set_orchestrator(orchestrator) -> None:
    """Initialize the tool with orchestrator instance.

    Args:
        orchestrator: AgentOrchestrator instance
    """
    global _orchestrator
    _orchestrator = orchestrator


async def check_subagent_results(explanation: str = "") -> str:
    """Check for pending subagent results and announcements.

    Args:
        explanation: Optional description of why results are being checked (shown in terminal)

    **IMPORTANT**: After spawning subagents, you MUST periodically call this tool
    to check if they have completed and retrieve their results. The results will
    contain valuable information that you should summarize for the user.

    This tool retrieves results from background tasks (subagents) that have
    completed since the last check. Use this:
    - After spawning subagents with spawn_subagent
    - Periodically while waiting for background tasks
    - When you expect a background task to have finished
    - Before responding to the user about task status

    Returns:
        String containing all pending announcements with task results, or a
        message if none are pending. When results are returned, you should
        naturally summarize them for the user in 1-2 sentences.

    Example:
        When a subagent completes analyzing files, this tool will return:
        "[Background Task Completed: 'file-analyzer']

        Task: Analyze all Python files in src/

        Result:
        Found 42 Python files with a total of 5,230 lines...

        Please summarize this result naturally for the user."

    Workflow Example:
        1. User asks: "Analyze file1.py and file2.py"
        2. You call: spawn_subagent(task="Analyze file1.py", label="analyzer-1")
        3. You call: spawn_subagent(task="Analyze file2.py", label="analyzer-2")
        4. You call: check_subagent_results() periodically
        5. When results arrive, you summarize: "File1 has been analyzed..."
    """
    if _orchestrator is None:
        return "Error: Subagent system not initialized"

    if not hasattr(_orchestrator, "_subagent_announcements"):
        return "No pending subagent results"

    announcements = _orchestrator._subagent_announcements

    if not announcements:
        return "No pending subagent results"

    # Build combined announcement
    messages = []
    for ann in announcements:
        messages.append(ann["announcement"])

    # Clear the queue
    _orchestrator._subagent_announcements.clear()

    # Return all announcements
    combined = "\n\n" + "=" * 60 + "\n\n".join(messages)

    return combined if messages else "No pending subagent results"
