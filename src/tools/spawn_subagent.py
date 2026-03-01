"""
Spawn subagent tool for parallel task execution.

This tool allows the main agent to create background subagents that execute
tasks in parallel. Subagents run with isolated tools (no recursive spawning)
and report results via events when complete.

Usage:
    The agent can use this tool to parallelize work:
    - Analyzing multiple files simultaneously
    - Running tests while writing documentation
    - Performing concurrent research tasks
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..subagents.manager import SubAgentManager

# Global references (injected by orchestrator during initialization)
_subagent_manager: "SubAgentManager | None" = None
_current_task_id: str = "main"


def set_subagent_manager(manager: "SubAgentManager", task_id: str = "main") -> None:
    """Initialize the spawn tool with manager instance.

    This function must be called during orchestrator initialization to
    connect the tool to the subagent management system.

    Args:
        manager: SubAgentManager instance to use for spawning
        task_id: Current task ID (defaults to "main")
    """
    global _subagent_manager, _current_task_id
    _subagent_manager = manager
    _current_task_id = task_id


async def spawn_subagent(
    task: str,
    label: str | None = None,
    explanation: str = "",
) -> str:
    """Spawn a background subagent to handle a task in parallel.

    The subagent will:
    - Run independently with isolated tools (no recursive spawning)
    - Execute up to 15 iterations maximum
    - Report results when completed via events
    - Have its own isolated state (no shared state with parent or other subagents)

    Use this tool for tasks that can be done concurrently, such as:
    - Analyzing different files or directories in parallel
    - Running tests while simultaneously writing documentation
    - Performing multiple independent research or analysis tasks
    - Executing long-running operations without blocking the main agent

    Args:
        task: Detailed description of what the subagent should accomplish.
            Be specific about the goal, inputs, and expected outputs.
        label: Optional short human-readable label for tracking this subagent
            (e.g., "test runner", "docs writer", "code analyzer").
            If not provided, defaults to "background task".
        explanation: Optional description of why this subagent is being spawned (shown in terminal)

    Returns:
        Confirmation message with the spawned subagent's unique ID

    Example:
        >>> result = await spawn_subagent(
        ...     task="Run all tests in the tests/ directory and report any failures",
        ...     label="test runner"
        ... )
        >>> print(result)
        "Subagent 'test runner' spawned (ID: 7f3a2b1c)"

    Note:
        - Subagents cannot spawn other subagents (spawn_subagent is not available to them)
        - Results are announced via events when the subagent completes
        - The parent agent can continue working while subagents run in the background
        - Maximum 15 iterations per subagent (vs 25 for main agent)
    """
    if _subagent_manager is None:
        return (
            "Error: Subagent system not initialized. This tool requires setup in the orchestrator."
        )

    return await _subagent_manager.spawn(
        task=task,
        label=label,
        parent_task_id=_current_task_id,
        max_iterations=15,
    )


# Tool metadata for AutoGen framework
# These attributes are read by the orchestrator to register the tool
spawn_subagent._tool_name = "spawn_subagent"  # type: ignore
spawn_subagent._tool_description = """Spawn a background subagent to handle a task in parallel.

The subagent runs independently with its own isolated state and tools, and reports results when done.
Use this for concurrent tasks like:
- Parallel file analysis (analyze multiple directories simultaneously)
- Simultaneous testing and documentation
- Independent research tasks
- Any long-running operation that shouldn't block the main agent

The subagent has access to most tools but cannot spawn additional subagents (prevents recursion).
Maximum 15 iterations per subagent."""  # type: ignore
