"""
Event system for subagent lifecycle management.

This module provides a lightweight event bus for communication between
parent tasks and spawned subagents. Events are published when subagents
are spawned, make progress, complete, or fail.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SubagentEvent:
    """Event representing a subagent lifecycle change.

    Attributes:
        subagent_id: Unique identifier for the subagent
        parent_task_id: ID of the parent task that spawned this subagent
        event_type: Type of event ("spawned", "progress", "completed", "failed")
        content: Event-specific data
        timestamp: Unix timestamp when event occurred
    """

    subagent_id: str
    parent_task_id: str
    event_type: str
    content: Any
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


class SubagentEventBus:
    """Lightweight event bus for subagent communication.

    This event bus allows parent tasks to subscribe to subagent lifecycle
    events. It maintains a history of events for debugging and replay.

    Example:
        >>> bus = SubagentEventBus()
        >>> async def on_complete(event):
        ...     print(f"Subagent {event.subagent_id} completed!")
        >>> bus.subscribe("completed", on_complete)
        >>> await bus.publish(SubagentEvent(
        ...     subagent_id="abc123",
        ...     parent_task_id="main",
        ...     event_type="completed",
        ...     content={"result": "Success"}
        ... ))
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: dict[str, list[Callable[[SubagentEvent], Awaitable[None]]]] = {}
        self._event_history: list[SubagentEvent] = []

    async def publish(self, event: SubagentEvent) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event to publish

        The event is added to history and all subscribers for the event type
        are notified asynchronously. Subscriber errors are caught and logged
        to prevent one subscriber from affecting others.
        """
        # Add to history
        self._event_history.append(event)

        # Notify subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        for callback in subscribers:
            try:
                await callback(event)
            except Exception as e:
                # Log error but don't stop other subscribers
                print(f"Error in event subscriber for {event.event_type}: {e}")

    def subscribe(
        self, event_type: str, callback: Callable[[SubagentEvent], Awaitable[None]]
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of events to subscribe to (e.g., "completed")
            callback: Async function to call when event is published

        Example:
            >>> async def handler(event):
            ...     print(f"Got event: {event.content}")
            >>> bus.subscribe("spawned", handler)
        """
        self._subscribers.setdefault(event_type, []).append(callback)

    def get_events_for_subagent(self, subagent_id: str) -> list[SubagentEvent]:
        """Get all historical events for a specific subagent.

        Args:
            subagent_id: ID of the subagent to query

        Returns:
            List of events for the specified subagent, in chronological order
        """
        return [e for e in self._event_history if e.subagent_id == subagent_id]

    def clear_history(self) -> None:
        """Clear the event history.

        This can be useful to free memory in long-running processes.
        Subscribers are not affected.
        """
        self._event_history.clear()
