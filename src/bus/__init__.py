"""
Message bus system for system-level messages and announcements.

Inspired by Nanobot's MessageBus architecture for auto-injection of
background task results into the agent conversation.
"""

from .message_bus import MessageBus, SystemMessage

__all__ = ["MessageBus", "SystemMessage"]
