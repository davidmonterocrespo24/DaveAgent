"""
Utilities for creating filtered tool sets for subagents.

This module provides helpers to create isolated tool environments for
subagents by filtering out specific tools (like spawn_subagent) to
prevent recursive spawning and other unwanted behaviors.
"""

from typing import Callable, Any


def create_tool_subset(
    all_tools: list[Callable],
    exclude_names: list[str] = None
) -> list[Callable]:
    """Create a filtered subset of tools by excluding specific names.

    This function is used to create isolated tool environments for subagents.
    For example, we exclude "spawn_subagent" from subagent tools to prevent
    infinite recursion.

    Args:
        all_tools: List of async functions that are tools
        exclude_names: Names of tools to exclude (e.g., ["spawn_subagent"])

    Returns:
        Filtered list of tools

    Example:
        >>> from src.tools import read_file, write_file, spawn_subagent
        >>> all_tools = [read_file, write_file, spawn_subagent]
        >>> subagent_tools = create_tool_subset(all_tools, ["spawn_subagent"])
        >>> len(subagent_tools)  # Only read_file and write_file
        2

    Note:
        This function works with the existing tool system that uses
        async functions directly, without requiring refactoring to
        class-based tools.
    """
    exclude_names = exclude_names or []

    filtered_tools = []
    for tool in all_tools:
        tool_name = tool.__name__
        if tool_name not in exclude_names:
            filtered_tools.append(tool)

    return filtered_tools


def get_tool_names(tools: list[Callable]) -> list[str]:
    """Get the names of all tools in a list.

    Args:
        tools: List of tool functions

    Returns:
        List of tool names (function names)

    Example:
        >>> from src.tools import read_file, write_file
        >>> tools = [read_file, write_file]
        >>> get_tool_names(tools)
        ['read_file', 'write_file']
    """
    return [tool.__name__ for tool in tools]
