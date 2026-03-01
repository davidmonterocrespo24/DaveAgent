"""
MessageBus for system-level announcements and auto-injection.

Inspired by Nanobot's MessageBus architecture. Provides a simple queue-based
system for injecting system messages (e.g., subagent results) into the
agent conversation automatically.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SystemMessage:
    """
    System-level message for auto-injection into agent conversation.

    Similar to Nanobot's InboundMessage but simplified for CodeAgent's needs.
    """

    message_type: str  # "subagent_result", "cron_result", etc.
    sender_id: str  # "subagent", "cron", etc.
    content: str  # Formatted announcement for the LLM

    # Routing info (optional, for future multi-session support)
    channel: str = "cli"
    chat_id: str = "default"

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "message_type": self.message_type,
            "sender_id": self.sender_id,
            "content": self.content,
            "channel": self.channel,
            "chat_id": self.chat_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class MessageBus:
    """
    Async message bus for system announcements.

    Provides a queue-based system where background tasks (subagents, cron jobs)
    can inject messages that the agent will automatically process.

    Similar to Nanobot's MessageBus but simplified:
    - Only inbound queue (no outbound needed for CLI-only CodeAgent)
    - No pub/sub (simple queue is sufficient)
    - Focus on auto-injection workflow
    """

    def __init__(self):
        """Initialize the message bus with an inbound queue."""
        self.inbound: asyncio.Queue[SystemMessage] = asyncio.Queue()
        self._message_count = 0
        logger.debug("MessageBus initialized")

    async def publish_inbound(self, message: SystemMessage) -> None:
        """
        Publish a system message to the inbound queue.

        This is called by background tasks (subagents, cron jobs) to inject
        their results into the agent conversation.

        Args:
            message: SystemMessage to inject
        """
        await self.inbound.put(message)
        self._message_count += 1
        logger.debug(
            f"Published {message.message_type} from {message.sender_id} "
            f"(total: {self._message_count})"
        )

    async def consume_inbound(self, timeout: float = 1.0) -> SystemMessage | None:
        """
        Consume the next inbound message from the queue.

        This is called by the agent loop to check for pending system messages.
        Non-blocking with configurable timeout.

        Args:
            timeout: Max time to wait for a message (seconds)

        Returns:
            SystemMessage if available, None if timeout
        """
        try:
            message = await asyncio.wait_for(self.inbound.get(), timeout=timeout)
            logger.debug(f"Consumed {message.message_type} from {message.sender_id}")
            return message
        except TimeoutError:
            return None

    def has_pending_messages(self) -> bool:
        """Check if there are pending messages without consuming."""
        return not self.inbound.empty()

    def get_pending_count(self) -> int:
        """Get the number of pending messages in the queue."""
        return self.inbound.qsize()

    def get_total_count(self) -> int:
        """Get the total number of messages published since creation."""
        return self._message_count
