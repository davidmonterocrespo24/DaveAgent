# Plan: Automatic Context Compression for Token Limit Management

**Date**: 2026-02-19
**Problem**: Agent crashes with `BadRequestError 400` when context exceeds model's maximum token limit (131,072 tokens for DeepSeek)
**User Request**: Implement automatic context compression/summarization when approaching token limits

---

## Problem Analysis

### Current Error

```
openai.BadRequestError: Error code: 400 - {'error': {'message': "This model's maximum context
length is 131072 tokens. However, you requested 140549 tokens (140549 in the messages, 0 in the
completion). Please reduce the length of the messages or completion."
```

### Root Cause

1. **BufferedChatCompletionContext** limits messages to 100 count, NOT tokens
2. **No token counting** before API calls - only tracking AFTER response
3. **No context compression** - old messages are dropped, not summarized
4. **No proactive monitoring** - system doesn't warn before hitting limits
5. **Sessions persist indefinitely** - long conversations accumulate context

### Current Context Management

**File**: `src/config/orchestrator.py` (lines 510-511)

```python
coder_context = BufferedChatCompletionContext(buffer_size=100)
planner_context = BufferedChatCompletionContext(buffer_size=100)
```

- Buffer size = 100 **messages** (not tokens!)
- When exceeded, oldest messages are dropped (FIFO)
- No summarization or compression

---

## Solution: Multi-Layered Context Management

Inspired by AutoGen's roadmap and Claude's automatic compaction, implement a **three-tier strategy**:

### Tier 1: Proactive Token Counting (IMMEDIATE)

Add `tiktoken` integration to count tokens BEFORE API calls and trigger compression when needed.

### Tier 2: Intelligent Context Compression (CORE)

When approaching token limits (e.g., 80% of max), automatically:
1. Summarize old messages using LLM
2. Replace message blocks with summaries
3. Preserve recent messages and system prompts

### Tier 3: Adaptive Buffer Sizing (ENHANCEMENT)

Dynamically adjust `BufferedChatCompletionContext` buffer size based on:
- Average tokens per message
- Model's context window
- Conversation complexity

---

## Implementation Plan

### Phase 1: Token Counting Infrastructure

**New File**: `src/utils/token_counter.py`

```python
"""Token counting utilities using tiktoken."""

import tiktoken
from typing import List, Dict, Any
from functools import lru_cache

@lru_cache(maxsize=10)
def get_encoder(model: str):
    """Get tiktoken encoder for model (cached)."""
    # Map model names to tiktoken encodings
    encoding_map = {
        "deepseek-chat": "cl100k_base",
        "deepseek-reasoner": "cl100k_base",
        "gpt-4": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
    }

    encoding_name = encoding_map.get(model, "cl100k_base")
    return tiktoken.get_encoding(encoding_name)

def count_message_tokens(messages: List[Dict[str, Any]], model: str) -> int:
    """Count tokens in message list.

    Args:
        messages: List of message dicts with role/content
        model: Model name for encoding selection

    Returns:
        Total token count
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
    """
    limits = {
        "deepseek-chat": 131072,
        "deepseek-reasoner": 131072,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
    }

    return limits.get(model, 4096)  # Conservative default

def should_compress_context(
    messages: List[Dict[str, Any]],
    model: str,
    threshold: float = 0.8
) -> bool:
    """Check if context should be compressed.

    Args:
        messages: Current message list
        model: Model name
        threshold: Percentage of max tokens to trigger compression (0.0-1.0)

    Returns:
        True if compression needed
    """
    current_tokens = count_message_tokens(messages, model)
    max_tokens = get_model_context_limit(model)

    usage_ratio = current_tokens / max_tokens
    return usage_ratio >= threshold
```

**Dependencies**: Add `tiktoken` to `requirements.txt`

---

### Phase 2: Context Compression Engine

**New File**: `src/utils/context_compressor.py`

```python
"""Context compression using LLM-based summarization."""

from typing import List, Dict, Any
from autogen_ext.models.openai import OpenAIChatCompletionClient

COMPRESSION_SYSTEM_PROMPT = """You are a conversation summarizer. Your task is to create a concise summary of the provided conversation messages while preserving:

1. Key information and context
2. Important decisions made
3. Tool calls and their results
4. User requests and agent responses
5. Current task state

Format your summary as a single comprehensive message that captures the essential conversation history."""

async def compress_message_block(
    messages: List[Dict[str, Any]],
    model_client: OpenAIChatCompletionClient,
    logger = None
) -> Dict[str, Any]:
    """Compress a block of messages into a single summary.

    Args:
        messages: List of messages to compress
        model_client: LLM client for summarization
        logger: Optional logger

    Returns:
        Single message dict containing summary
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
                "compression_timestamp": None  # Add timestamp if needed
            }
        }

    except Exception as e:
        if logger:
            logger.error(f"Compression failed: {e}")
        # Fallback: simple truncation message
        return {
            "role": "system",
            "content": f"[{len(messages)} messages removed due to context limits]"
        }

def select_messages_to_compress(
    messages: List[Dict[str, Any]],
    keep_recent: int = 20
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Select which messages to compress vs keep.

    Strategy:
    - Keep system prompts (role="system")
    - Keep recent N messages
    - Compress everything else in the middle

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

    # Split into old (compress) and recent (keep)
    messages_to_compress = non_system_messages[:-keep_recent]
    messages_to_keep = system_messages + non_system_messages[-keep_recent:]

    return messages_to_compress, messages_to_keep

async def compress_context_if_needed(
    messages: List[Dict[str, Any]],
    model: str,
    model_client: OpenAIChatCompletionClient,
    logger = None,
    compression_threshold: float = 0.8,
    keep_recent: int = 20
) -> List[Dict[str, Any]]:
    """Main compression function - compress context if needed.

    Args:
        messages: Current message list
        model: Model name for token counting
        model_client: LLM client for summarization
        logger: Optional logger
        compression_threshold: Token usage ratio to trigger compression
        keep_recent: Number of recent messages to preserve

    Returns:
        Compressed message list (or original if no compression needed)
    """
    from src.utils.token_counter import should_compress_context, count_message_tokens

    if not should_compress_context(messages, model, compression_threshold):
        return messages  # No compression needed

    if logger:
        tokens_before = count_message_tokens(messages, model)
        logger.warning(
            f"Context approaching token limit ({tokens_before} tokens). "
            f"Compressing older messages..."
        )

    # Select messages for compression
    to_compress, to_keep = select_messages_to_compress(messages, keep_recent)

    if not to_compress:
        return messages  # Nothing to compress

    # Compress old messages into summary
    summary = await compress_message_block(to_compress, model_client, logger)

    # Reconstruct message list: [system prompts] + [summary] + [recent messages]
    system_messages = [msg for msg in to_keep if msg.get("role") == "system"]
    recent_messages = [msg for msg in to_keep if msg.get("role") != "system"]

    compressed_messages = system_messages + [summary] + recent_messages

    if logger:
        tokens_after = count_message_tokens(compressed_messages, model)
        logger.info(
            f"Context compressed: {len(messages)} messages ({tokens_before} tokens) → "
            f"{len(compressed_messages)} messages ({tokens_after} tokens)"
        )

    return compressed_messages
```

---

### Phase 3: Integration with Model Clients

**File**: `src/utils/logging_model_client.py` (lines 70-95)

**Current Code**:

```python
async def create(self, messages: Sequence[LLMMessage], **kwargs: Any) -> CreateResult:
    """Intercept create calls to log them."""

    # Process messages (convert to dicts)
    processed_messages = self._process_messages(messages)

    # Call wrapped client
    result = await self._wrapped.create(messages=processed_messages, **kwargs)
```

**Add Compression Before API Call**:

```python
async def create(self, messages: Sequence[LLMMessage], **kwargs: Any) -> CreateResult:
    """Intercept create calls to log them and compress context if needed."""

    # Process messages (convert to dicts)
    processed_messages = self._process_messages(messages)

    # CONTEXT COMPRESSION: Check if compression needed
    from src.utils.context_compressor import compress_context_if_needed
    from src.utils.token_counter import count_message_tokens, get_model_context_limit

    model = kwargs.get("model") or self._wrapped._model

    # Log token usage BEFORE compression
    tokens_before = count_message_tokens(processed_messages, model)
    max_tokens = get_model_context_limit(model)

    self.logger.debug(
        f"[{self._agent_name}] Context tokens: {tokens_before}/{max_tokens} "
        f"({(tokens_before/max_tokens)*100:.1f}%)"
    )

    # Compress if needed (threshold: 80% of max)
    compressed_messages = await compress_context_if_needed(
        messages=processed_messages,
        model=model,
        model_client=self._wrapped,  # Use wrapped client for summarization
        logger=self.logger,
        compression_threshold=0.80,  # Trigger at 80% capacity
        keep_recent=20  # Keep last 20 messages uncompressed
    )

    # Log if compression occurred
    if len(compressed_messages) != len(processed_messages):
        tokens_after = count_message_tokens(compressed_messages, model)
        self.logger.info(
            f"[{self._agent_name}] Context compressed: "
            f"{len(processed_messages)} → {len(compressed_messages)} messages "
            f"({tokens_before} → {tokens_after} tokens)"
        )

    # Call wrapped client with compressed messages
    result = await self._wrapped.create(messages=compressed_messages, **kwargs)

    # ... rest of logging code ...
```

---

### Phase 4: Error Recovery for Token Limit

**File**: `src/main.py` (around error handling in `process_user_request`)

**Add Specific Handler for Token Limit Errors**:

```python
except Exception as e:
    error_str = str(e)

    # Check if it's a token limit error (BadRequestError 400)
    if "maximum context length" in error_str.lower() or "140549 tokens" in error_str:
        self.logger.error(
            "🚨 Token limit exceeded! This should have been prevented by compression. "
            "Forcing emergency context cleanup..."
        )

        # Emergency fallback: Clear agent context and retry with truncated history
        try:
            # Reset agent contexts to clear accumulated messages
            from autogen_core.model_context import BufferedChatCompletionContext

            self.coder_agent._model_context = BufferedChatCompletionContext(buffer_size=50)
            self.planning_agent._model_context = BufferedChatCompletionContext(buffer_size=50)

            self.cli.print_warning(
                "⚠️ Context exceeded maximum tokens. Conversation history was compressed. "
                "Continuing with recent messages only..."
            )

            self.logger.info("Agent contexts reset to buffer_size=50. Retrying request...")

            # Don't retry automatically - inform user
            self.cli.print_error(
                "Please rephrase your request or start a new session with /new-session"
            )

        except Exception as reset_error:
            self.logger.error(f"Failed to reset contexts: {reset_error}")

    # Existing error handling for other errors...
```

---

### Phase 5: Configuration Options

**File**: `src/config/settings.py`

**Add Context Management Settings**:

```python
class Settings:
    # ... existing settings ...

    # Context management settings
    context_compression_enabled: bool = True
    context_compression_threshold: float = 0.80  # Compress at 80% of max tokens
    context_keep_recent_messages: int = 20       # Keep last N messages uncompressed
    context_buffer_size: int = 100               # Max messages in buffer

    # Token limits per model
    model_token_limits: dict = {
        "deepseek-chat": 131072,
        "deepseek-reasoner": 131072,
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 4096,
    }
```

---

## Critical Files to Modify

1. **src/utils/token_counter.py** (NEW) - Token counting with tiktoken
2. **src/utils/context_compressor.py** (NEW) - LLM-based compression
3. **src/utils/logging_model_client.py** (MODIFY) - Add compression before API calls
4. **src/main.py** (MODIFY) - Add token limit error recovery
5. **src/config/settings.py** (MODIFY) - Add compression configuration
6. **requirements.txt** (MODIFY) - Add `tiktoken` dependency

---

## Testing Strategy

### Test 1: Token Counting Accuracy

```python
# Test that token counting matches OpenAI's actual usage
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]

counted_tokens = count_message_tokens(messages, "deepseek-chat")
# Should be close to actual API usage
```

### Test 2: Compression Trigger

```python
# Create conversation that exceeds 80% of token limit
# Verify compression is triggered automatically
# Confirm resulting message count is reduced
```

### Test 3: Summary Quality

```python
# Compress a conversation block
# Verify summary preserves key information
# Check that summary is significantly shorter than original
```

### Test 4: Error Recovery

```python
# Force a token limit error
# Verify emergency fallback activates
# Confirm graceful degradation
```

---

## Expected Outcomes

1. **Proactive Prevention**: Context compressed BEFORE hitting token limits
2. **Graceful Degradation**: If limits hit, emergency cleanup prevents crashes
3. **Transparency**: User notified when compression occurs
4. **Configurability**: Settings allow tuning compression behavior
5. **Performance**: Minimal overhead from token counting (cached encoders)

---

## Alternative Approaches Considered

### Alternative 1: Retrieval-Based (MemGPT)

**Pros**: Very sophisticated, maintains long-term memory
**Cons**: Complex integration, requires vector DB, overkill for current needs

### Alternative 2: Simple Truncation

**Pros**: Fast, simple to implement
**Cons**: Loses important context, breaks conversation coherence

### Alternative 3: Sliding Window

**Pros**: Maintains recent context
**Cons**: No compression of old messages, still wastes tokens

**Selected Approach**: LLM-based compression (balance of quality and complexity)

---

## Implementation Checklist

- [ ] Create `src/utils/token_counter.py` with tiktoken integration
- [ ] Create `src/utils/context_compressor.py` with LLM summarization
- [ ] Modify `src/utils/logging_model_client.py` to add compression
- [ ] Add token limit error recovery in `src/main.py`
- [ ] Add configuration settings in `src/config/settings.py`
- [ ] Add `tiktoken` to `requirements.txt`
- [ ] Test token counting accuracy
- [ ] Test compression trigger at 80% threshold
- [ ] Test summary quality preservation
- [ ] Test error recovery fallback
- [ ] Document compression behavior for users
