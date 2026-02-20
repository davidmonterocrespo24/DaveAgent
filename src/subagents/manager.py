"""
SubAgent Manager - Core component for parallel subagent execution.

This module manages the lifecycle of spawned subagents, providing:
- Background task execution using asyncio.Task
- Isolated tool environments to prevent recursive spawning
- Event-driven communication with parent tasks
- Automatic cleanup of completed tasks
"""

import asyncio
import logging
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
        message_bus=None,  # Optional MessageBus for auto-injection
        max_concurrent: int = 10,  # Maximum concurrent subagents
    ):
        """Initialize the SubAgent Manager.

        Args:
            event_bus: Event bus for publishing subagent lifecycle events
            orchestrator_factory: Factory function that creates AgentOrchestrator
                instances. Should accept: tools (list), max_iterations (int),
                mode (str)
            base_tools: List of all available tools. spawn_subagent will be
                filtered out for subagents to prevent recursion
            message_bus: Optional MessageBus for auto-injection of results
            max_concurrent: Maximum number of concurrent subagents (default: 10)
        """
        self.event_bus = event_bus
        self.orchestrator_factory = orchestrator_factory
        self.base_tools = base_tools
        self.message_bus = message_bus  # NEW: For auto-injection
        self.max_concurrent = max_concurrent  # NEW: Limit concurrent subagents
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._results: dict[str, dict] = {}
        self.logger = logging.getLogger("DaveAgent")  # Initialize logger

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
        # Check concurrent limit
        if len(self._running_tasks) >= self.max_concurrent:
            raise RuntimeError(
                f"Maximum concurrent subagents ({self.max_concurrent}) reached. "
                f"Wait for some to complete before spawning more. "
                f"Currently running: {len(self._running_tasks)}"
            )

        subagent_id = str(uuid.uuid4())[:8]
        label = label or "background task"

        # Log subagent spawn (DEBUG only - detailed logging for files)
        self.logger.debug(f"[MAIN] Spawning subagent: ID={subagent_id}, label='{label}'")
        self.logger.debug(f"[MAIN] Subagent task: {task[:200]}{'...' if len(task) > 200 else ''}")
        self.logger.debug(f"[MAIN] Max iterations: {max_iterations}, Parent task: {parent_task_id}")

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
        self.logger.debug(f"[{subagent_id}] Starting subagent execution")
        self.logger.debug(f"[{subagent_id}] Task: {task}")
        self.logger.debug(f"[{subagent_id}] Label: '{label}', Max iterations: {max_iterations}")

        try:
            # Create isolated tools - remove spawn_subagent to prevent recursion
            isolated_tools = create_tool_subset(
                self.base_tools,
                exclude_names=["spawn_subagent"]
            )

            self.logger.debug(f"[{subagent_id}] Created isolated toolset with {len(isolated_tools)} tools")

            # Create isolated orchestrator instance using factory pattern
            # This ensures each subagent has its own state
            orchestrator = self.orchestrator_factory(
                tools=isolated_tools,
                max_iterations=max_iterations,
                mode="subagent",  # Signals simplified execution (no full UI)
                task=task,  # Pass task for subagent-specific system prompt
                subagent_id=subagent_id,  # Pass unique ID for logging differentiation
            )

            self.logger.debug(f"[{subagent_id}] Orchestrator created, starting task execution...")

            # Run the task using existing AgentOrchestrator logic
            result = await orchestrator.run_task(task)

            self.logger.debug(f"[{subagent_id}] Task completed successfully")
            self.logger.debug(f"[{subagent_id}] Result length: {len(result)} chars")
            self.logger.debug(f"[{subagent_id}] Result preview: {result[:200]}{'...' if len(result) > 200 else ''}")

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

            # NEW: Auto-inject result into conversation via MessageBus (Nanobot-style)
            if self.message_bus:
                await self._inject_result(subagent_id, label, task, result, "ok")

        except Exception as e:
            # Log error details (DEBUG only)
            self.logger.error(f"[{subagent_id}] Subagent failed with error: {type(e).__name__}: {str(e)}")
            self.logger.debug(f"[{subagent_id}] Full traceback:", exc_info=True)

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

            # NEW: Auto-inject failure into conversation via MessageBus (Nanobot-style)
            if self.message_bus:
                error_msg = f"Error: {str(e)}"
                await self._inject_result(subagent_id, label, task, error_msg, "error")

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

    async def _inject_result(
        self,
        subagent_id: str,
        label: str,
        task: str,
        result: str,
        status: str
    ) -> None:
        """
        Inject subagent result into the conversation via MessageBus (Nanobot-style).

        This is the auto-injection mechanism that makes results appear automatically
        in the agent conversation without requiring the agent to call check_subagent_results.

        Args:
            subagent_id: Subagent identifier
            label: Human-readable label
            task: Original task description
            result: Result or error message
            status: "ok" or "error"
        """
        from src.bus import SystemMessage

        # Format announcement similar to Nanobot's style
        status_text = "completed successfully" if status == "ok" else "failed"

        announce_content = f"""[Background Task '{label}' {status_text}]

Task: {task}

Result:
{result}

Please summarize this naturally for the user. Keep it brief (1-2 sentences).
Do not mention technical details like "subagent" or task IDs."""

        # Create system message for injection
        sys_msg = SystemMessage(
            message_type="subagent_result",
            sender_id=f"subagent:{subagent_id}",
            content=announce_content,
            metadata={
                "subagent_id": subagent_id,
                "label": label,
                "status": status,
            }
        )

        # Inject into MessageBus
        await self.message_bus.publish_inbound(sys_msg)
