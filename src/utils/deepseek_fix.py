"""
Configuration for using DeepSeek Reasoner (R1) with thinking mode

IMPLEMENTED SOLUTION:
Use DeepSeekReasoningClient which wraps OpenAIChatCompletionClient
to properly handle the reasoning_content field required by DeepSeek R1.

The client:
1. Enables thinking mode automatically for deepseek-reasoner
2. Injects extra_body={"thinking": {"type": "enabled"}} when necessary
3. Caches reasoning_content to preserve it in tool calls

Based on:
- https://api-docs.deepseek.com/guides/thinking_mode
- https://docs.ag2.ai/docs/api/autogen_ext.models.openai
"""


def should_use_reasoning_client(settings):
    """
    Determines if we should use DeepSeekReasoningClient for this model.

    Args:
        settings: Configuration object with model attribute

    Returns:
        bool: True if we should use the reasoning client
    """
    # Use reasoning client for deepseek-reasoner or deepseek-chat
    return settings.model in ("deepseek-reasoner", "deepseek-chat", "deepseek-r1")


def get_thinking_mode_enabled(model: str) -> bool:
    """
    Determines if thinking mode should be enabled for this model.

    Args:
        model: Model name

    Returns:
        bool: True if thinking mode should be enabled
    """
    # Enable automatically for deepseek-reasoner and deepseek-r1
    return model in ("deepseek-reasoner", "deepseek-r1")

