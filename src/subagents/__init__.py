"""
Subagent system for parallel task execution.

This package provides infrastructure for spawning and managing subagents
that run tasks in parallel with isolated state and tools.

Main components:
- SubagentEventBus: Event system for subagent lifecycle communication
- SubAgentManager: Manager for spawning and tracking subagents
- Tool utilities: Helpers for creating isolated tool sets
"""

from .events import SubagentEvent, SubagentEventBus
from .manager import SubAgentManager
from .tool_wrapper import create_tool_subset, get_tool_names

__all__ = [
    "SubagentEvent",
    "SubagentEventBus",
    "SubAgentManager",
    "create_tool_subset",
    "get_tool_names",
]
