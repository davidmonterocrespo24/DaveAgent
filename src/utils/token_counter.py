"""Token counting utilities using tiktoken.

This module provides utilities for counting tokens in messages before sending
them to LLM APIs. This enables proactive context management and compression
to prevent token limit errors.
"""

from functools import lru_cache
from typing import Any

import tiktoken


@lru_cache(maxsize=10)
def get_encoder(model: str):
    """Get tiktoken encoder for model (cached).

    Args:
        model: Model name (e.g., "deepseek-chat", "gpt-4")

    Returns:
        tiktoken.Encoding instance for the model

    Note:
        Results are cached to avoid repeatedly loading encoders.
    """
    # Map model names to tiktoken encodings
    encoding_map = {
        "deepseek-chat": "cl100k_base",
        "deepseek-reasoner": "cl100k_base",
        "gpt-4": "cl100k_base",
        "gpt-4-32k": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-3.5-turbo-16k": "cl100k_base",
    }

    encoding_name = encoding_map.get(model, "cl100k_base")
    return tiktoken.get_encoding(encoding_name)


def count_message_tokens(messages: list[dict[str, Any]], model: str) -> int:
    """Count tokens in message list.

    This function approximates the token count that will be sent to the API.
    It includes:
    - Message structure overhead (role, content keys)
    - Role tokens
    - Content tokens (text and multi-modal)
    - Tool call tokens
    - Response priming tokens

    Args:
        messages: List of message dicts with role/content
        model: Model name for encoding selection

    Returns:
        Total token count (approximate)

    Example:
        >>> messages = [
        ...     {"role": "user", "content": "Hello"},
        ...     {"role": "assistant", "content": "Hi there!"}
        ... ]
        >>> count_message_tokens(messages, "deepseek-chat")
        15
    """
    encoder = get_encoder(model)
    total_tokens = 0

    for message in messages:
        # Add tokens for message structure (role, content keys, etc.)
        total_tokens += 4  # Message overhead

        # Count role tokens
        if "role" in message:
            total_tokens += len(encoder.encode(message["role"]))

        # Count content tokens
        if "content" in message:
            content = message["content"]
            if isinstance(content, str):
                total_tokens += len(encoder.encode(content))
            elif isinstance(content, list):
                # Handle multi-modal content (text + images)
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        total_tokens += len(encoder.encode(item["text"]))
                    # Note: Image tokens are not counted here (model-specific)

        # Count function call tokens (tool calls)
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                total_tokens += len(encoder.encode(str(tool_call)))

    total_tokens += 2  # Add for response priming
    return total_tokens


def get_model_context_limit(model: str) -> int:
    """Get maximum context tokens for model.

    Args:
        model: Model name

    Returns:
        Maximum context window size in tokens

    Note:
        Returns a conservative default (4096) for unknown models.
    """
    limits = {
        "deepseek-chat": 131072,
        "deepseek-reasoner": 131072,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
    }

    return limits.get(model, 4096)  # Conservative default


def should_compress_context(
    messages: list[dict[str, Any]], model: str, threshold: float = 0.8
) -> bool:
    """Check if context should be compressed.

    Args:
        messages: Current message list
        model: Model name
        threshold: Percentage of max tokens to trigger compression (0.0-1.0)

    Returns:
        True if compression needed (token usage >= threshold)

    Example:
        >>> messages = [...]  # Many messages
        >>> should_compress_context(messages, "deepseek-chat", threshold=0.8)
        True  # If using >= 80% of 131K tokens
    """
    current_tokens = count_message_tokens(messages, model)
    max_tokens = get_model_context_limit(model)

    usage_ratio = current_tokens / max_tokens
    return usage_ratio >= threshold


def get_token_usage_stats(messages: list[dict[str, Any]], model: str) -> dict[str, Any]:
    """Get detailed token usage statistics.

    Args:
        messages: Current message list
        model: Model name

    Returns:
        Dict with:
            - current_tokens: Current token count
            - max_tokens: Maximum allowed tokens
            - usage_ratio: Percentage used (0.0-1.0)
            - messages_count: Number of messages
            - avg_tokens_per_message: Average tokens per message

    Example:
        >>> stats = get_token_usage_stats(messages, "deepseek-chat")
        >>> print(f"Using {stats['usage_ratio']*100:.1f}% of context")
        Using 65.2% of context
    """
    current_tokens = count_message_tokens(messages, model)
    max_tokens = get_model_context_limit(model)
    usage_ratio = current_tokens / max_tokens
    messages_count = len(messages)
    avg_tokens = current_tokens / messages_count if messages_count > 0 else 0

    return {
        "current_tokens": current_tokens,
        "max_tokens": max_tokens,
        "usage_ratio": usage_ratio,
        "messages_count": messages_count,
        "avg_tokens_per_message": avg_tokens,
    }
