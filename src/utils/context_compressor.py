"""Context compression using LLM-based summarization with advanced features.

This module implements intelligent context compression inspired by gemini-cli:
- Tool output truncation with file saving
- XML-structured state snapshots
- Verification with probe (second LLM turn)
- Anti-inflation validation
- Persistent failure tracking
- Smart message splitting
"""

from typing import List, Dict, Any, Tuple, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dataclasses import dataclass
import asyncio


# Import new utilities
from src.utils.compression_prompts import (
    get_compression_prompt,
    get_probe_prompt,
    get_anchor_instruction,
    extract_snapshot_from_history,
)
from src.utils.tool_output_truncator import (
    truncate_tool_output_if_needed,
    cleanup_old_outputs,
)


# Configuration constants
DEFAULT_COMPRESSION_THRESHOLD = 0.5  # 50% of model limit
DEFAULT_KEEP_RECENT = 30  # Increased from 20
DEFAULT_TOOL_TRUNCATE_THRESHOLD = 40000  # 40K characters
DEFAULT_MAX_SUMMARY_TOKENS = 4000  # Max tokens for state_snapshot


@dataclass
class CompressionState:
    """Track compression state to avoid costly retries after failures.

    Attributes:
        has_failed_compression: True if last compression failed or inflated tokens
        compression_threshold: Configurable threshold (0.0-1.0)
        tool_truncate_threshold: Character limit for tool outputs
        enable_probe: Whether to use verification step
        max_summary_tokens: Maximum tokens for summary
    """
    has_failed_compression: bool = False
    compression_threshold: float = DEFAULT_COMPRESSION_THRESHOLD
    tool_truncate_threshold: int = DEFAULT_TOOL_TRUNCATE_THRESHOLD
    enable_probe: bool = True
    max_summary_tokens: int = DEFAULT_MAX_SUMMARY_TOKENS


@dataclass
class CompressionResult:
    """Result of a compression attempt.

    Attributes:
        compressed_messages: New message list (or None if failed)
        original_token_count: Token count before compression
        new_token_count: Token count after compression
        compression_failed: True if compression failed
        failure_reason: Reason for failure (if any)
        tokens_saved: Number of tokens saved
    """
    compressed_messages: Optional[List[Dict[str, Any]]]
    original_token_count: int
    new_token_count: int
    compression_failed: bool = False
    failure_reason: Optional[str] = None
    tokens_saved: int = 0


async def truncate_tool_outputs_in_messages(
    messages: List[Dict[str, Any]],
    tool_counter: dict,
    threshold: int = DEFAULT_TOOL_TRUNCATE_THRESHOLD,
    logger=None
) -> List[Dict[str, Any]]:
    """Truncate large tool outputs in messages, saving full content to disk.

    Args:
        messages: List of messages to process
        tool_counter: Counter for generating unique tool IDs
        threshold: Character threshold for truncation
        logger: Optional logger

    Returns:
        Messages with truncated tool outputs
    """
    truncated_messages = []

    for msg in messages:
        new_msg = msg.copy()

        # Check if this is a tool result message
        if msg.get("role") == "tool":
            content = msg.get("content", "")

            if isinstance(content, str) and len(content) > threshold:
                # Generate unique ID for this tool output
                tool_name = msg.get("name", "unknown_tool")
                tool_id = tool_counter.get(tool_name, 0)
                tool_counter[tool_name] = tool_id + 1

                # Truncate and save
                truncated_content, was_truncated, saved_path = await truncate_tool_output_if_needed(
                    content,
                    tool_name,
                    f"{tool_id:03d}",
                    threshold
                )

                if was_truncated and logger:
                    logger.debug(f"Truncated {tool_name} output: {len(content)} → {len(truncated_content)} chars")
                    if saved_path:
                        logger.debug(f"  Full output saved to: {saved_path}")

                new_msg["content"] = truncated_content

        truncated_messages.append(new_msg)

    return truncated_messages


def find_safe_split_point(
    messages: List[Dict[str, Any]],
    target_ratio: float = 0.7
) -> int:
    """Find safe point to split messages, avoiding tool call/response breaks.

    Args:
        messages: Message list
        target_ratio: Target ratio for compression (0.7 = compress first 70%)

    Returns:
        Index where to split (messages[:idx] will be compressed)
    """
    target_idx = int(len(messages) * target_ratio)

    # Search backwards for a safe split point (user message)
    for i in range(target_idx, -1, -1):
        msg = messages[i]

        # Only split at user messages
        if msg.get("role") != "user":
            continue

        # Check if there are pending tool calls after this message
        has_pending_tools = False
        for j in range(i + 1, len(messages)):
            if messages[j].get("role") == "assistant" and messages[j].get("tool_calls"):
                # Found tool call, check if it has responses
                tool_call_ids = [tc.get("id") for tc in messages[j].get("tool_calls", [])]

                # Look for tool responses
                for k in range(j + 1, len(messages)):
                    if messages[k].get("role") == "tool":
                        tool_call_id = messages[k].get("tool_call_id")
                        if tool_call_id in tool_call_ids:
                            tool_call_ids.remove(tool_call_id)

                # If any tool calls don't have responses, don't split here
                if tool_call_ids:
                    has_pending_tools = True
                    break

        if not has_pending_tools:
            return i

    # Fallback: don't compress anything if no safe point found
    return 0


async def compress_message_block_with_verification(
    messages: List[Dict[str, Any]],
    model_client: OpenAIChatCompletionClient,
    model: str,
    state: CompressionState,
    logger=None
) -> CompressionResult:
    """Compress messages with XML state_snapshot and verification probe.

    Args:
        messages: Messages to compress
        model_client: LLM client
        model: Model name
        state: Compression state
        logger: Optional logger

    Returns:
        CompressionResult with compressed messages or failure info
    """
    from src.utils.token_counter import count_message_tokens

    if logger:
        logger.info(f"Compressing {len(messages)} messages with state_snapshot format...")

    # Count original tokens
    original_tokens = count_message_tokens(messages, model)

    # Format messages for summarization
    conversation_text = "\n\n".join([
        f"[{msg.get('role', 'unknown')}]: {msg.get('content', '')}"
        for msg in messages
        if msg.get('content')
    ])

    # Check if previous snapshot exists for anchoring
    previous_snapshot = extract_snapshot_from_history(messages)

    # Construct summarization request
    if previous_snapshot:
        # Use anchor instruction to build on previous snapshot
        user_prompt = get_anchor_instruction(previous_snapshot)
        user_prompt += f"\n\nRecent conversation history:\n{conversation_text}"
    else:
        user_prompt = f"Summarize this conversation:\n\n{conversation_text}\n\nFirst, reason in your scratchpad. Then, generate the <state_snapshot>."

    # Convert to LLMMessage objects
    from autogen_core.models import SystemMessage, UserMessage, AssistantMessage

    summary_messages = [
        SystemMessage(content=get_compression_prompt()),
        UserMessage(content=user_prompt, source="user")
    ]

    try:
        # PHASE 1: Generate initial state_snapshot
        result = await model_client.create(
            messages=summary_messages,
            extra_create_args={
                "temperature": 0.3,
                "max_tokens": state.max_summary_tokens
            }
        )

        summary_content = result.content

        if not summary_content or len(summary_content.strip()) == 0:
            # Empty summary - compression failed
            if logger:
                logger.error("Compression failed: empty summary generated")

            return CompressionResult(
                compressed_messages=None,
                original_token_count=original_tokens,
                new_token_count=original_tokens,
                compression_failed=True,
                failure_reason="empty_summary"
            )

        # PHASE 2: Verification probe (if enabled)
        if state.enable_probe:
            if logger:
                logger.debug("Running verification probe...")

            verification_messages = summary_messages + [
                AssistantMessage(content=summary_content, source="assistant"),
                UserMessage(content=get_probe_prompt(), source="user")
            ]

            verification_result = await model_client.create(
                messages=verification_messages,
                extra_create_args={
                    "temperature": 0.3,
                    "max_tokens": state.max_summary_tokens
                }
            )

            # Use verified summary if available, otherwise fall back to original
            final_summary = verification_result.content or summary_content
        else:
            final_summary = summary_content

        # Construct summary message
        summary_msg = {
            "role": "user",  # User role for state_snapshot
            "content": final_summary
        }

        # Construct acknowledgment from assistant
        ack_msg = {
            "role": "assistant",
            "content": "Got it. Thanks for the additional context! I'll continue from here."
        }

        # Calculate token count of new summary
        new_tokens = count_message_tokens([summary_msg, ack_msg], model)

        # VALIDATION: Anti-inflation check
        if new_tokens >= original_tokens:
            if logger:
                logger.warning(
                    f"⚠️ Compression rejected: inflated tokens "
                    f"({original_tokens} → {new_tokens})"
                )

            return CompressionResult(
                compressed_messages=None,
                original_token_count=original_tokens,
                new_token_count=new_tokens,
                compression_failed=True,
                failure_reason="token_inflation"
            )

        # SUCCESS: Compression reduced tokens
        tokens_saved = original_tokens - new_tokens

        if logger:
            logger.info(
                f"✓ Compression successful: {len(messages)} messages ({original_tokens} tokens) → "
                f"state_snapshot ({new_tokens} tokens), saved {tokens_saved} tokens"
            )

        return CompressionResult(
            compressed_messages=[summary_msg, ack_msg],
            original_token_count=original_tokens,
            new_token_count=new_tokens,
            compression_failed=False,
            tokens_saved=tokens_saved
        )

    except Exception as e:
        if logger:
            logger.error(f"Compression failed with exception: {e}")

        return CompressionResult(
            compressed_messages=None,
            original_token_count=original_tokens,
            new_token_count=original_tokens,
            compression_failed=True,
            failure_reason=f"exception: {str(e)}"
        )


def select_messages_to_compress(
    messages: List[Dict[str, Any]],
    keep_recent: int = DEFAULT_KEEP_RECENT
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Select which messages to compress vs keep using smart splitting.

    Strategy:
    - Keep ALL system prompts (role="system") - never compress these
    - Keep recent N messages for immediate context
    - Compress everything else in the middle
    - Use smart splitting to avoid breaking tool call/response pairs
    - CRITICAL: Preserve reasoning_content field for DeepSeek Reasoner compatibility

    Args:
        messages: Full message list
        keep_recent: Number of recent messages to preserve

    Returns:
        Tuple of (messages_to_compress, messages_to_keep)
    """
    system_messages = [msg for msg in messages if msg.get("role") == "system"]
    non_system_messages = [msg for msg in messages if msg.get("role") != "system"]

    if len(non_system_messages) <= keep_recent:
        # Not enough messages to compress
        return [], messages

    # Find safe split point
    split_idx = find_safe_split_point(non_system_messages, target_ratio=0.7)

    if split_idx == 0:
        # No safe split point found
        return [], messages

    # Split into old (compress) and recent (keep)
    messages_to_compress = non_system_messages[:split_idx]
    messages_to_keep = system_messages + non_system_messages[split_idx:]

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
    state: Optional[CompressionState] = None
) -> List[Dict[str, Any]]:
    """Main compression function - compress context if needed.

    This is the primary entry point for context compression. It:
    1. Checks if compression is needed (based on token threshold)
    2. Truncates large tool outputs, saving to disk
    3. Selects messages to compress (old) vs keep (recent + system)
    4. Calls LLM to create XML state_snapshot with verification
    5. Validates that compression reduces tokens (anti-inflation)
    6. Reconstructs message list with summary replacing old messages

    Args:
        messages: Current message list
        model: Model name for token counting
        model_client: LLM client for summarization
        logger: Optional logger
        state: Optional compression state (creates default if None)

    Returns:
        Compressed message list (or original if no compression needed/failed)

    Example:
        >>> state = CompressionState()
        >>> compressed = await compress_context_if_needed(
        ...     messages=all_messages,
        ...     model="deepseek-chat",
        ...     model_client=client,
        ...     logger=logger,
        ...     state=state
        ... )
    """
    from src.utils.token_counter import should_compress_context, count_message_tokens

    # Create default state if not provided
    if state is None:
        state = CompressionState()

    # Check if compression is needed
    if not should_compress_context(messages, model, state.compression_threshold):
        return messages  # No compression needed

    if logger:
        tokens_before = count_message_tokens(messages, model)
        logger.warning(
            f"⚠️ Context approaching token limit ({tokens_before} tokens). "
            f"Compressing older messages..."
        )

    # If previous compression failed, use simple truncation only
    if state.has_failed_compression:
        if logger:
            logger.info("Previous compression failed, using truncation-only mode")

        # Just keep recent messages
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        non_system = [msg for msg in messages if msg.get("role") != "system"]

        truncated = system_messages + non_system[-DEFAULT_KEEP_RECENT:]

        tokens_after = count_message_tokens(truncated, model)

        if logger:
            logger.info(
                f"✓ Truncation complete: {len(messages)} → {len(truncated)} messages, "
                f"{tokens_before} → {tokens_after} tokens"
            )

        return truncated

    # STEP 1: Truncate tool outputs
    tool_counter = {}
    messages = await truncate_tool_outputs_in_messages(
        messages,
        tool_counter,
        state.tool_truncate_threshold,
        logger
    )

    # Cleanup old tool output files (keep last 100)
    cleanup_old_outputs(max_files=100)

    # STEP 2: Select messages for compression
    to_compress, to_keep = select_messages_to_compress(
        messages,
        keep_recent=DEFAULT_KEEP_RECENT
    )

    if not to_compress:
        if logger:
            logger.debug("No messages to compress (all are recent or system prompts)")
        return messages  # Nothing to compress

    # STEP 3: Compress with verification
    result = await compress_message_block_with_verification(
        to_compress,
        model_client,
        model,
        state,
        logger
    )

    if result.compression_failed:
        # Mark failure and fall back to truncation
        state.has_failed_compression = True

        if logger:
            logger.warning(
                f"Compression failed ({result.failure_reason}), falling back to truncation"
            )

        # Simple truncation fallback
        system_messages = [msg for msg in to_keep if msg.get("role") == "system"]
        non_system = [msg for msg in to_keep if msg.get("role") != "system"]

        # Keep only system + recent
        truncated = system_messages + non_system

        return truncated

    # STEP 4: Reconstruct message list
    system_messages = [msg for msg in to_keep if msg.get("role") == "system"]
    recent_messages = [msg for msg in to_keep if msg.get("role") != "system"]

    compressed_messages = (
        system_messages +
        result.compressed_messages +
        recent_messages
    )

    # CRITICAL FIX: Ensure all assistant messages in final list have reasoning_content if needed
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
    keep_recent: int = DEFAULT_KEEP_RECENT
) -> float:
    """Estimate compression ratio if compression were applied.

    Args:
        messages: Current message list
        keep_recent: Number of recent messages to preserve

    Returns:
        Estimated compression ratio (e.g., 0.25 = 75% reduction)
    """
    to_compress, to_keep = select_messages_to_compress(messages, keep_recent)

    if not to_compress:
        return 1.0  # No compression possible

    # Estimate: summary counts as 2 messages (state_snapshot + ack)
    compressed_count = len(to_keep) + 2
    original_count = len(messages)

    return compressed_count / original_count
