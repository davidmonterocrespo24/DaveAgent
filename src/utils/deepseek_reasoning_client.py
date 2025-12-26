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
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from autogen_core import CancellationToken
from autogen_core.models import CreateResult, LLMMessage, RequestUsage
from autogen_core.tools import Tool, ToolSchema
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._openai_client import (
    FunctionCall,
    convert_tool_choice,
    convert_tools,
    to_oai_type,
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
        self._raw_responses: list[dict[str, Any]] = []

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
            oai_messages = self._normalize_messages(oai_messages)
            oai_messages = self._inject_reasoning_content(oai_messages)

            # CRITICAL Fix for "Invalid consecutive assistant message":
            # DeepSeek API forbids the last message from being 'assistant'.
            # If the last message is from the assistant, we must append a user message.
            if oai_messages and oai_messages[-1].get("role") == "assistant":
                oai_messages.append(
                    {
                        "role": "user",
                        "content": "Continue",
                    }
                )

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
            try:
                completion = await self._client.chat.completions.create(**request_params)
            except Exception as e:
                # Log detailed message dump on BadRequestError to help debug
                if "BadRequestError" in str(type(e)) or "400" in str(e):
                    import json

                    self.logger.error(
                        "❌ BadRequestError detected! Dumping messages for debugging:"
                    )
                    self.logger.error(
                        json.dumps(request_params.get("messages", []), indent=2, default=str)
                    )
                raise e

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

    def _inject_reasoning_content(self, oai_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                # CRITICAL Fix for "Invalid consecutive assistant message":
                # Only inject reasoning_content if the message has tool_calls.
                # Injecting reasoning into pure text messages in history causes API errors.
                if not msg.get("tool_calls"):
                    modified_messages.append(modified_msg)
                    continue

                # Try to match this message with a raw response
                for raw_resp in reversed(self._raw_responses):
                    # Match by tool_calls ONLY (since content matching is risky for history)
                    if self._messages_match_tools(msg, raw_resp):
                        reasoning = raw_resp.get("reasoning_content")
                        if reasoning:
                            modified_msg["reasoning_content"] = reasoning
                            self.logger.debug("💭 Injected reasoning_content for tool call")
                        break

            modified_messages.append(modified_msg)

        return modified_messages

    def _messages_match_tools(self, msg: dict[str, Any], raw_resp: dict[str, Any]) -> bool:
        """Check if message matches raw response by tool calls."""
        msg_tool_calls = msg.get("tool_calls", [])
        raw_tool_calls = raw_resp.get("tool_calls", [])

        if msg_tool_calls and raw_tool_calls:
            try:
                msg_ids = {tc.get("id") for tc in msg_tool_calls if tc.get("id")}
                raw_ids = {tc.get("id") for tc in raw_tool_calls if tc.get("id")}
                return msg_ids and msg_ids == raw_ids
            except Exception:
                return False
        return False

    def _messages_match(self, msg: dict[str, Any], raw_resp: dict[str, Any]) -> bool:
        # Kept for backward compatibility but unused by injection now
        return self._messages_match_tools(msg, raw_resp)

    def clear_reasoning_cache(self):
        """Clear stored reasoning_content (useful for new conversations)."""
        count = len(self._raw_responses)
        self._raw_responses.clear()
        self.logger.debug(f"🧹 Cleared {count} raw responses")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about stored reasoning_content."""
        return {
            "raw_responses": len(self._raw_responses),
            "raw_responses_with_reasoning": sum(
                1 for r in self._raw_responses if r.get("reasoning_content")
            ),
        }

    def _normalize_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Merge consecutive assistant messages to satisfy API requirements.
        DeepSeek (and OpenAI) do not allow consecutive assistant messages.
        """
        if not messages:
            return messages

        # DEBUG: Log input message roles
        roles = [m.get("role") for m in messages]
        self.logger.debug(f"Input messages for normalization: {roles}")

        normalized = []

        for msg in messages:
            # Skip messages with None role
            if not msg.get("role"):
                continue

            # DeepSeek Fix: Strip 'name' from user messages to prevent role confusion
            # The API might treat named user messages (e.g. name='Coder') as assistant-like
            if msg.get("role") == "user" and "name" in msg:
                del msg["name"]

            if not normalized:
                normalized.append(msg)
                continue

            last_msg = normalized[-1]

            # Check for consecutive assistant messages
            if msg.get("role") == "assistant" and last_msg.get("role") == "assistant":
                # Merge content
                c1 = last_msg.get("content")
                c2 = msg.get("content")

                if c1 and c2:
                    last_msg["content"] = str(c1) + "\n\n" + str(c2)
                else:
                    last_msg["content"] = c1 or c2 or ""

                # Merge tool calls
                tc1 = last_msg.get("tool_calls", [])
                tc2 = msg.get("tool_calls", [])

                if tc2:
                    # If last_msg had no tool_calls, initialize it
                    if not tc1:
                        last_msg["tool_calls"] = list(tc2)  # Copy to be safe
                    else:
                        # Append new tool calls
                        last_msg["tool_calls"].extend(tc2)

                # Merge reasoning_content if present
                rc1 = last_msg.get("reasoning_content")
                rc2 = msg.get("reasoning_content")

                if rc2:
                    if rc1:
                        last_msg["reasoning_content"] = str(rc1) + "\n\n" + str(rc2)
                    else:
                        last_msg["reasoning_content"] = rc2
            else:
                normalized.append(msg)

        # DEBUG: Log normalized roles
        norm_roles = [m.get("role") for m in normalized]
        self.logger.debug(f"Normalized roles (pre-fix): {norm_roles}")

        return self._fix_broken_tool_chains(normalized)

    def _fix_broken_tool_chains(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Fix broken tool chains where A(tool_calls) is followed by a user message
        instead of a tool output. This happens when the system interrupts
        execution (e.g. for approval).

        Strategy: Strip 'tool_calls' from the assistant message, making it a
        pure text message.
        """
        if not messages:
            return messages

        fixed_messages = []
        for i, msg in enumerate(messages):
            # Create a copy to match the output structure of previous processing
            # (although simple dict copy is enough as we modify dicts)
            current_msg = msg.copy()

            # Check if this is an assistant message with tool calls
            if current_msg.get("role") == "assistant" and current_msg.get("tool_calls"):
                # Look ahead to the next message
                if i + 1 < len(messages):
                    next_msg = messages[i + 1]
                    # If next message is NOT a tool response (function or tool role),
                    # then the chain is broken.
                    if next_msg.get("role") not in ["tool", "function"]:
                        self.logger.warning(
                            f"🔧 Fixing broken tool chain at index {i}. "
                            f"Next role is {next_msg.get('role')}, expected 'tool'."
                        )
                        # Strip tool calls to convert to text message
                        del current_msg["tool_calls"]
                else:
                    # Trailing assistant message with tool calls is valid
                    # (it's the one currently being generated or waiting for response)
                    pass

            # 1. Ensure content is string if present (some clients send None)
            if "content" in current_msg and current_msg["content"] is None:
                current_msg["content"] = ""

            # 2. If tool_calls is empty list, remove it
            if "tool_calls" in current_msg and not current_msg["tool_calls"]:
                del current_msg["tool_calls"]

            # 3. Handle messages with empty content
            if not current_msg.get("content") and "tool_calls" not in current_msg:
                current_msg["content"] = ""

            fixed_messages.append(current_msg)

        # DEBUG: Log fixed msg roles
        fixed_roles = [m.get("role") for m in fixed_messages]
        self.logger.debug(f"Fixed roles: {fixed_roles}")

        return fixed_messages
