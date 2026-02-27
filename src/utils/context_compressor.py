"""Context compression using LLM-based summarization.

This module implements intelligent context compression to prevent token limit errors.
When conversations grow too long, old messages are automatically summarized using
the LLM itself, preserving key information while reducing token count.
"""

from typing import List, Dict, Any, Tuple
from autogen_ext.models.openai import OpenAIChatCompletionClient


COMPRESSION_SYSTEM_PROMPT = """You are a conversation summarizer. Your task is to create a concise summary of the provided conversation messages while preserving:

1. Key information and context
2. Important decisions made
3. Tool calls and their results
4. User requests and agent responses
5. Current task state

Format your summary as a single comprehensive message that captures the essential conversation history.
Focus on factual information and avoid unnecessary details.
"""


async def compress_message_block(
    messages: List[Dict[str, Any]],
    model_client: OpenAIChatCompletionClient,
    logger=None
) -> Dict[str, Any]:
    """Compress a block of messages into a single summary.

    Uses the LLM itself to create an intelligent summary of the conversation,
    preserving key information while drastically reducing token count.

    Args:
        messages: List of messages to compress
        model_client: LLM client for summarization
        logger: Optional logger for debugging

    Returns:
        Single message dict containing summary with metadata

    Example:
        >>> summary = await compress_message_block(old_messages, client)
        >>> print(summary['content'])
        [CONVERSATION SUMMARY - 45 messages compressed]

        User requested to analyze Python code...
        Agent found 3 bugs and fixed them...
    """
    if logger:
        logger.info(f"Compressing {len(messages)} messages...")

    # Format messages for summarization
    conversation_text = "\n\n".join([
        f"[{msg.get('role', 'unknown')}]: {msg.get('content', '')}"
        for msg in messages
        if msg.get('content')
    ])

    # Request summary from LLM
    summary_messages = [
        {"role": "system", "content": COMPRESSION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Summarize this conversation:\n\n{conversation_text}"}
    ]

    try:
        result = await model_client.create(
            messages=summary_messages,
            temperature=0.3,  # Lower temperature for consistent summaries
            max_tokens=2000   # Limit summary length
        )

        summary_content = result.content

        if logger:
            logger.info(f"Compression complete: {len(messages)} messages → 1 summary")

        return {
            "role": "system",
            "content": f"[CONVERSATION SUMMARY - {len(messages)} messages compressed]\n\n{summary_content}",
            "metadata": {
                "compressed": True,
                "original_message_count": len(messages),
                "compression_timestamp": None  # Can add timestamp if needed
            }
        }

    except Exception as e:
        if logger:
            logger.error(f"Compression failed: {e}")

        # Fallback: simple truncation message
        return {
            "role": "system",
            "content": f"[{len(messages)} messages removed due to context limits]",
            "metadata": {
                "compressed": True,
                "original_message_count": len(messages),
                "compression_failed": True
            }
        }


def select_messages_to_compress(
    messages: List[Dict[str, Any]],
    keep_recent: int = 20
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Select which messages to compress vs keep.

    Strategy:
    - Keep ALL system prompts (role="system") - never compress these
    - Keep recent N messages for immediate context
    - Compress everything else in the middle
    - CRITICAL: Preserve reasoning_content field for DeepSeek Reasoner compatibility

    Args:
        messages: Full message list
        keep_recent: Number of recent messages to preserve

    Returns:
        Tuple of (messages_to_compress, messages_to_keep)

    Example:
        >>> to_compress, to_keep = select_messages_to_compress(all_messages, 20)
        >>> print(f"Compressing {len(to_compress)} old messages")
        >>> print(f"Keeping {len(to_keep)} messages (system + recent)")
    """
    system_messages = [msg for msg in messages if msg.get("role") == "system"]
    non_system_messages = [msg for msg in messages if msg.get("role") != "system"]

    if len(non_system_messages) <= keep_recent:
        # Not enough messages to compress
        return [], messages

    # Split into old (compress) and recent (keep)
    messages_to_compress = non_system_messages[:-keep_recent]
    messages_to_keep = system_messages + non_system_messages[-keep_recent:]

    # CRITICAL FIX: Ensure reasoning_content is preserved for DeepSeek Reasoner
    # Per DeepSeek API requirement: assistant messages with tool_calls MUST have reasoning_content
    # Reference: https://api-docs.deepseek.com/guides/thinking_mode#tool-calls
    for msg in messages_to_keep:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            # If reasoning_content is missing, add empty string placeholder
            if "reasoning_content" not in msg:
                msg["reasoning_content"] = ""

    return messages_to_compress, messages_to_keep


async def compress_context_if_needed(
    messages: List[Dict[str, Any]],
    model: str,
    model_client: OpenAIChatCompletionClient,
    logger=None,
    compression_threshold: float = 0.8,
    keep_recent: int = 20
) -> List[Dict[str, Any]]:
    """Main compression function - compress context if needed.

    This is the primary entry point for context compression. It:
    1. Checks if compression is needed (based on token threshold)
    2. Selects messages to compress (old) vs keep (recent + system)
    3. Calls LLM to create summary of old messages
    4. Reconstructs message list with summary replacing old messages

    Args:
        messages: Current message list
        model: Model name for token counting
        model_client: LLM client for summarization
        logger: Optional logger
        compression_threshold: Token usage ratio to trigger compression (default: 0.8)
        keep_recent: Number of recent messages to preserve (default: 20)

    Returns:
        Compressed message list (or original if no compression needed)

    Example:
        >>> compressed = await compress_context_if_needed(
        ...     messages=all_messages,
        ...     model="deepseek-chat",
        ...     model_client=client,
        ...     logger=logger
        ... )
        >>> # If compression occurred:
        >>> # compressed = [system_prompts] + [summary] + [last 20 messages]
    """
    from src.utils.token_counter import should_compress_context, count_message_tokens

    if not should_compress_context(messages, model, compression_threshold):
        return messages  # No compression needed

    if logger:
        tokens_before = count_message_tokens(messages, model)
        logger.warning(
            f"⚠️ Context approaching token limit ({tokens_before} tokens). "
            f"Compressing older messages..."
        )

    # Select messages for compression
    to_compress, to_keep = select_messages_to_compress(messages, keep_recent)

    if not to_compress:
        if logger:
            logger.debug("No messages to compress (all are recent or system prompts)")
        return messages  # Nothing to compress

    # Compress old messages into summary
    summary = await compress_message_block(to_compress, model_client, logger)

    # Reconstruct message list: [system prompts] + [summary] + [recent messages]
    system_messages = [msg for msg in to_keep if msg.get("role") == "system"]
    recent_messages = [msg for msg in to_keep if msg.get("role") != "system"]

    compressed_messages = system_messages + [summary] + recent_messages

    # CRITICAL FIX: Ensure all assistant messages in final list have reasoning_content if needed
    # This is essential for DeepSeek Reasoner compatibility after compression
    for msg in compressed_messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            if "reasoning_content" not in msg:
                msg["reasoning_content"] = ""

    if logger:
        tokens_after = count_message_tokens(compressed_messages, model)
        logger.info(
            f"✓ Context compressed: {len(messages)} messages ({tokens_before} tokens) → "
            f"{len(compressed_messages)} messages ({tokens_after} tokens)"
        )

    return compressed_messages


def estimate_compression_ratio(
    messages: List[Dict[str, Any]],
    keep_recent: int = 20
) -> float:
    """Estimate compression ratio if compression were applied.

    Args:
        messages: Current message list
        keep_recent: Number of recent messages to preserve

    Returns:
        Estimated compression ratio (e.g., 0.25 = 75% reduction)

    Example:
        >>> ratio = estimate_compression_ratio(messages, 20)
        >>> print(f"Compression would reduce context by {(1-ratio)*100:.0f}%")
        Compression would reduce context by 70%
    """
    to_compress, to_keep = select_messages_to_compress(messages, keep_recent)

    if not to_compress:
        return 1.0  # No compression possible

    # Estimate: summary counts as 1 message
    compressed_count = len(to_keep) + 1
    original_count = len(messages)

    return compressed_count / original_count
