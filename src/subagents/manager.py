"""
SubAgent Manager - Core component for parallel subagent execution.

This module manages the lifecycle of spawned subagents, providing:
- Background task execution using asyncio.Task
- Isolated tool environments to prevent recursive spawning
- Event-driven communication with parent tasks
- Automatic cleanup of completed tasks
"""

import asyncio
import uuid
from typing import Callable, Any
from datetime import datetime

from .events import SubagentEventBus, SubagentEvent
from .tool_wrapper import create_tool_subset


class SubAgentManager:
    """Manager for spawning and tracking parallel subagents.

    This manager creates isolated orchestrator instances for each subagent,
    allowing them to run in parallel without sharing state. Each subagent
    has its own tool set (with spawn_subagent removed to prevent recursion)
    and communicates completion/failure via the event bus.

    Key Design:
    - Uses factory pattern to create isolated AgentOrchestrator instances
    - Each subagent runs as an independent asyncio.Task
    - No shared state between subagents
    - Automatic cleanup via done callbacks

    Example:
        >>> event_bus = SubagentEventBus()
        >>> manager = SubAgentManager(
        ...     event_bus=event_bus,
        ...     orchestrator_factory=create_orchestrator,
        ...     base_tools=[read_file, write_file, spawn_subagent]
        ... )
        >>> result = await manager.spawn(
        ...     task="Analyze all Python files in src/",
        ...     label="code analyzer"
        ... )
        >>> print(result)
        "Subagent 'code analyzer' spawned (ID: abc12345)"
    """

    def __init__(
        self,
        event_bus: SubagentEventBus,
        orchestrator_factory: Callable,
        base_tools: list[Callable],
    ):
        """Initialize the SubAgent Manager.

        Args:
            event_bus: Event bus for publishing subagent lifecycle events
            orchestrator_factory: Factory function that creates AgentOrchestrator
                instances. Should accept: tools (list), max_iterations (int),
                mode (str)
            base_tools: List of all available tools. spawn_subagent will be
                filtered out for subagents to prevent recursion
        """
        self.event_bus = event_bus
        self.orchestrator_factory = orchestrator_factory
        self.base_tools = base_tools
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._results: dict[str, dict] = {}

    async def spawn(
        self,
        task: str,
        label: str = None,
        parent_task_id: str = "main",
        max_iterations: int = 15,
    ) -> str:
        """Spawn a background subagent to execute a task in parallel.

        This creates a new asyncio.Task that runs independently with its own
        isolated orchestrator instance and tool set.

        Args:
            task: Detailed description of what the subagent should accomplish
            label: Human-readable label for tracking (defaults to "background task")
            parent_task_id: ID of parent task for event routing
            max_iterations: Maximum iterations for the subagent (default 15)

        Returns:
            Confirmation message with the spawned subagent's ID

        Example:
            >>> await manager.spawn(
            ...     task="Run all unit tests and report failures",
            ...     label="test runner",
            ...     max_iterations=10
            ... )
            "Subagent 'test runner' spawned (ID: 7f3a2b1c)"
        """
        subagent_id = str(uuid.uuid4())[:8]
        label = label or "background task"

        # Create background asyncio task
        bg_task = asyncio.create_task(
            self._run_subagent(
                subagent_id=subagent_id,
                task=task,
                label=label,
                parent_task_id=parent_task_id,
                max_iterations=max_iterations,
            ),
            name=f"subagent_{label}_{subagent_id}"
        )

        # Store task reference
        self._running_tasks[subagent_id] = bg_task

        # Auto-cleanup when done
        bg_task.add_done_callback(
            lambda _: self._running_tasks.pop(subagent_id, None)
        )

        # Publish spawn event
        await self.event_bus.publish(SubagentEvent(
            subagent_id=subagent_id,
            parent_task_id=parent_task_id,
            event_type="spawned",
            content={"task": task, "label": label}
        ))

        return f"Subagent '{label}' spawned (ID: {subagent_id})"

    async def _run_subagent(
        self,
        subagent_id: str,
        task: str,
        label: str,
        parent_task_id: str,
        max_iterations: int,
    ) -> None:
        """Execute subagent in isolated context (internal method).

        This method:
        1. Creates isolated tools (removes spawn_subagent)
        2. Creates isolated orchestrator via factory
        3. Runs the task
        4. Publishes completion/failure events
        5. Stores result for later retrieval

        Args:
            subagent_id: Unique ID for this subagent
            task: Task to execute
            label: Human-readable label
            parent_task_id: Parent task ID for event routing
            max_iterations: Max iterations allowed
        """
        try:
            # Create isolated tools - remove spawn_subagent to prevent recursion
            isolated_tools = create_tool_subset(
                self.base_tools,
                exclude_names=["spawn_subagent"]
            )

            # Create isolated orchestrator instance using factory pattern
            # This ensures each subagent has its own state
            orchestrator = self.orchestrator_factory(
                tools=isolated_tools,
                max_iterations=max_iterations,
                mode="subagent",  # Signals simplified execution (no full UI)
                task=task,  # Pass task for subagent-specific system prompt
            )

            # Run the task using existing AgentOrchestrator logic
            result = await orchestrator.run_task(task)

            # Store successful result
            self._results[subagent_id] = {
                "status": "ok",
                "result": result,
                "label": label,
            }

            # Publish completion event
            await self.event_bus.publish(SubagentEvent(
                subagent_id=subagent_id,
                parent_task_id=parent_task_id,
                event_type="completed",
                content={
                    "label": label,
                    "task": task,  # Include task for better context
                    "result": result,
                    "status": "ok"
                }
            ))

        except Exception as e:
            # Store error result
            self._results[subagent_id] = {
                "status": "error",
                "error": str(e),
                "label": label,
            }

            # Publish failure event
            await self.event_bus.publish(SubagentEvent(
                subagent_id=subagent_id,
                parent_task_id=parent_task_id,
                event_type="failed",
                content={
                    "label": label,
                    "error": str(e),
                    "status": "error"
                }
            ))

    async def get_status(self, subagent_id: str) -> dict:
        """Get current status of a subagent.

        Args:
            subagent_id: ID of the subagent to query

        Returns:
            Dictionary with status information:
            - status: "running", "completed", or "not_found"
            - result: Task result (if completed successfully)
            - error: Error message (if failed)
            - label: Subagent label
            - done: Boolean indicating if task is complete

        Example:
            >>> status = await manager.get_status("abc12345")
            >>> if status["status"] == "completed":
            ...     print(status["result"])
        """
        task = self._running_tasks.get(subagent_id)

        if task is None:
            # Check if we have cached result from completed task
            if subagent_id in self._results:
                return {
                    "status": "completed",
                    **self._results[subagent_id]
                }
            return {"status": "not_found"}

        # Task exists but may or may not be done
        if task.done():
            return {
                "status": "completed",
                **self._results.get(subagent_id, {})
            }

        return {
            "status": "running",
            "done": False,
        }

    def list_active_subagents(self) -> list[dict]:
        """List all currently running subagents.

        Returns:
            List of dictionaries with subagent info:
            - id: Subagent ID
            - status: "running"

        Example:
            >>> active = manager.list_active_subagents()
            >>> for sa in active:
            ...     print(f"Subagent {sa['id']} is {sa['status']}")
        """
        return [
            {
                "id": subagent_id,
                "status": "running",
            }
            for subagent_id, task in self._running_tasks.items()
            if not task.done()
        ]

    async def cancel_all(self) -> None:
        """Cancel all running subagents.

        This is useful for cleanup when the parent task is cancelled
        or when shutting down the system.

        Example:
            >>> await manager.cancel_all()
        """
        tasks_to_cancel = list(self._running_tasks.values())

        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()

        # Wait for all cancellations to complete
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
