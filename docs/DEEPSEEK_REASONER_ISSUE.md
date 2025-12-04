# DeepSeek Reasoner + AutoGen Compatibility Issue

## Problem Description

**Error Message:**
```
Error code: 400 - {'error': {'message': 'Missing `reasoning_content` field in the assistant message at message index X'}}
```

**Root Cause:**
DeepSeek's Reasoner model (`deepseek-reasoner` or `deepseek-chat` with thinking mode enabled) uses a special field called `reasoning_content` to store the model's chain-of-thought reasoning. When using **tool calls** (function calling), the DeepSeek API requires that:

1. **Every assistant message that contains tool_calls MUST include the `reasoning_content` field**
2. This `reasoning_content` must be preserved when constructing the message history for subsequent API calls

AutoGen (version 0.7.5) **does not preserve** the `reasoning_content` field when reconstructing conversation history. This causes the error when an agent tries to use tools multiple times in a conversation.

## Technical Details

### How DeepSeek Reasoner Works

According to [DeepSeek's documentation](https://api-docs.deepseek.com/guides/thinking_mode#tool-calls):

```python
# Response structure
response.choices[0].message = {
    "role": "assistant",
    "content": "Final answer text",
    "reasoning_content": "Chain of thought reasoning...",  # ← This field!
    "tool_calls": [...]
}
```

When continuing a conversation with tool calls, you MUST pass back the entire message object including `reasoning_content`:

```python
# Correct way (from DeepSeek docs)
messages.append(response.choices[0].message)  # Includes reasoning_content
```

### Why AutoGen Fails

AutoGen's internal message handling:
1. Converts OpenAI SDK responses to AutoGen's `LLMMessage` objects
2. **Strips out non-standard fields** like `reasoning_content`
3. Reconstructs messages from history without `reasoning_content`
4. Sends incomplete messages back to DeepSeek API → **400 error**

## Current Solution

**Automatic workaround applied:** The system automatically detects when you try to use `deepseek-reasoner` and switches to `deepseek-chat` instead.

### What This Means

✅ **Works:**
- Full tool calling support with DeepSeek
- All agent features functional
- Multiple tool calls in sequence
- Complete conversation history

✗ **Limited:**
- No extended reasoning mode (thinking mode)
- Model uses standard inference instead of showing reasoning process

### Configuration

The fix is applied automatically in [main.py:75-83](../main.py#L75-L83):

```python
from src.utils.deepseek_fix import disable_deepseek_thinking_mode
if disable_deepseek_thinking_mode(self.settings):
    # Automatically switches from deepseek-reasoner to deepseek-chat
    pass
```

## Future Solutions

### Option 1: Wait for AutoGen Update
AutoGen maintainers need to add support for preserving custom fields like `reasoning_content` in message history.

**Status:** Not yet implemented in autogen-ext 0.7.5

### Option 2: Custom Client Implementation
We've created `DeepSeekReasonerClient` in [src/utils/deepseek_reasoner_client.py](../src/utils/deepseek_reasoner_client.py) that attempts to preserve `reasoning_content`, but it requires deeper integration with AutoGen's internals.

**Status:** Experimental, not fully functional yet

### Option 3: Monkey Patch AutoGen
Patch AutoGen's message reconstruction to preserve `reasoning_content`.

**Status:** Risky, not recommended for production

## How to Use DeepSeek Reasoner (Future)

Once AutoGen adds support, you'll be able to use:

```python
# Method 1: Use deepseek-reasoner model
model_client = OpenAIChatCompletionClient(
    model="deepseek-reasoner",
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# Method 2: Enable thinking mode with deepseek-chat
model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    api_key=api_key,
    base_url="https://api.deepseek.com",
    extra_body={"thinking": {"type": "enabled"}}
)
```

## Testing

To test the current workaround:

```bash
# This will automatically use deepseek-chat instead of deepseek-reasoner
python main.py
```

Try a request that uses multiple tool calls:
```
User: List files in src directory, then count how many Python files there are
```

The agent will successfully use multiple tools without the `reasoning_content` error.

## References

- [DeepSeek Thinking Mode Documentation](https://api-docs.deepseek.com/guides/thinking_mode)
- [DeepSeek Tool Calls with Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode#tool-calls)
- [AutoGen-ext GitHub](https://github.com/microsoft/autogen)
- [Issue Report](https://github.com/microsoft/autogen/issues/XXXXX) _(to be created)_

## Summary

**TL;DR:** DeepSeek Reasoner with tool calls is currently not compatible with AutoGen. The system automatically uses `deepseek-chat` as a workaround, which provides full functionality except for the extended reasoning feature.

---

_Last updated: 2025-12-04_
_Affects: AutoGen 0.7.5, DeepSeek API_
