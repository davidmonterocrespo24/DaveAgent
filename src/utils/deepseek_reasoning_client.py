"""
DeepSeek Reasoning Client - Optimized version for DeepSeek R1 with reasoning mode

This client solves the "Missing reasoning_content field" error when using
DeepSeek Reasoner with tool calls by:
1. Intercepting message conversion to inject reasoning_content from cache
2. Storing raw API responses to preserve reasoning_content
3. Calling OpenAI client directly to avoid AutoGen stripping custom fields

Based on: https://api-docs.deepseek.com/guides/thinking_mode#tool-calls
"""

import logging
from typing import Any, Dict, Sequence, Mapping, Literal, List

from autogen_core import CancellationToken
from autogen_core.models import LLMMessage, CreateResult, RequestUsage
from autogen_core.tools import Tool, ToolSchema
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._openai_client import (
    to_oai_type,
    convert_tools,
    convert_tool_choice,
    FunctionCall,
)
from pydantic import BaseModel


class DeepSeekReasoningClient(OpenAIChatCompletionClient):
    """
    Client for DeepSeek R1 that preserves reasoning_content in tool call workflows.

    Usage:
        client = DeepSeekReasoningClient(
            model="deepseek-reasoner",
            api_key="your-api-key",
            base_url="https://api.deepseek.com",
            model_capabilities=get_model_capabilities()
        )
    """

    def __init__(self, *args, enable_thinking: bool = None, **kwargs):
        """
        Args:
            enable_thinking: If True, enables thinking mode. Auto-detected if None.
        """
        model = kwargs.get("model", args[0] if args else None)

        # Auto-enable thinking for deepseek-reasoner
        if enable_thinking is None:
            enable_thinking = model == "deepseek-reasoner"

        self.enable_thinking = enable_thinking
        self.logger = logging.getLogger(__name__)

        # Store raw API responses with reasoning_content
        self._raw_responses: List[Dict[str, Any]] = []

        super().__init__(*args, **kwargs)

       

    async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        tool_choice: Tool | Literal["auto", "required", "none"] = "auto",
        json_output: bool | type[BaseModel] | None = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: CancellationToken | None = None,
    ) -> CreateResult:
        """
        Override create() to inject reasoning_content before API calls.
        """
        # Add thinking mode to extra_create_args
        modified_extra_args = dict(extra_create_args)
        if self.enable_thinking:
            if "extra_body" not in modified_extra_args:
                modified_extra_args["extra_body"] = {}
            if "thinking" not in modified_extra_args["extra_body"]:
                modified_extra_args["extra_body"]["thinking"] = {"type": "enabled"}
                self.logger.debug("💭 Thinking mode enabled")

        try:
            # Convert messages to OpenAI format
            oai_messages = []
            for msg in messages:
                oai_msg = to_oai_type(msg)
                # to_oai_type returns a list, flatten it
                if isinstance(oai_msg, list):
                    oai_messages.extend(oai_msg)
                else:
                    oai_messages.append(oai_msg)

            # Inject reasoning_content from previous responses
            oai_messages = self._inject_reasoning_content(oai_messages)

            # Prepare API request parameters
            request_params = {
                "model": self._create_args["model"],
                "messages": oai_messages,
                **modified_extra_args,
            }

            # Add tools if provided
            if tools:
                request_params["tools"] = convert_tools(tools)
                request_params["tool_choice"] = convert_tool_choice(tool_choice)

            # Call OpenAI API directly
            completion = await self._client.chat.completions.create(**request_params)

            # Extract and store the response
            raw_message = completion.choices[0].message
            reasoning_content = getattr(raw_message, "reasoning_content", None)

            # Store raw response for future injection
            raw_dict = {"role": "assistant", "content": raw_message.content or ""}
            if reasoning_content:
                raw_dict["reasoning_content"] = reasoning_content
                self.logger.info(f"💭 Reasoning: {len(reasoning_content)} chars")
            if raw_message.tool_calls:
                raw_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in raw_message.tool_calls
                ]

            self._raw_responses.append(raw_dict)

            # Convert to AutoGen CreateResult
            if raw_message.tool_calls:
                content = [
                    FunctionCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments)
                    for tc in raw_message.tool_calls
                ]
            else:
                content = raw_message.content or ""

            usage = None
            if completion.usage:
                usage = RequestUsage(
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                )

            # Map DeepSeek's "tool_calls" to AutoGen's "function_calls"
            finish_reason = completion.choices[0].finish_reason or "stop"
            if finish_reason == "tool_calls":
                finish_reason = "function_calls"

            return CreateResult(
                finish_reason=finish_reason,
                content=content,
                usage=usage,
                cached=False,
            )

        except Exception as e:
            self.logger.error(f"❌ DeepSeek call failed: {e}")
            raise

    def _inject_reasoning_content(self, oai_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inject reasoning_content into assistant messages before sending to API.

        This is the critical fix: DeepSeek requires reasoning_content in assistant
        messages when using tool calls.
        """
        if not self._raw_responses:
            return oai_messages

        modified_messages = []
        for msg in oai_messages:
            modified_msg = dict(msg)

            # Only inject into assistant messages
            if msg.get("role") == "assistant":
                # Try to match this message with a raw response
                for raw_resp in reversed(self._raw_responses):
                    # Match by content or tool_calls
                    if self._messages_match(msg, raw_resp):
                        reasoning = raw_resp.get("reasoning_content")
                        if reasoning:
                            modified_msg["reasoning_content"] = reasoning
                            self.logger.debug("💭 Injected reasoning_content")
                        break

            modified_messages.append(modified_msg)

        return modified_messages

    def _messages_match(self, msg: Dict[str, Any], raw_resp: Dict[str, Any]) -> bool:
        """Check if a message matches a raw response."""
        # Match by content
        if msg.get("content") and msg.get("content") == raw_resp.get("content"):
            return True

        # Match by tool_calls
        msg_tool_calls = msg.get("tool_calls", [])
        raw_tool_calls = raw_resp.get("tool_calls", [])
        if msg_tool_calls and raw_tool_calls:
            msg_ids = {tc.get("id") for tc in msg_tool_calls if tc.get("id")}
            raw_ids = {tc.get("id") for tc in raw_tool_calls if tc.get("id")}
            return msg_ids and msg_ids == raw_ids

        return False

    def clear_reasoning_cache(self):
        """Clear stored reasoning_content (useful for new conversations)."""
        count = len(self._raw_responses)
        self._raw_responses.clear()
        self.logger.debug(f"🧹 Cleared {count} raw responses")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about stored reasoning_content."""
        return {
            "raw_responses": len(self._raw_responses),
            "raw_responses_with_reasoning": sum(
                1 for r in self._raw_responses if r.get("reasoning_content")
            ),
        }
