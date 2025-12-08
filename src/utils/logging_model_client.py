"""
Logging Model Client Wrapper - Intercepts LLM calls for logging

This wrapper is placed around the real model_client and captures:
- Messages sent to the LLM (input)
- Responses received from the LLM (output)
- Token usage
- Timing

Records everything in the JSONLogger for complete traceability.
"""
import logging
from autogen_core.models import ChatCompletionClient, RequestUsage
from autogen_core.models import (
    LLMMessage,
    CreateResult,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    FunctionExecutionResultMessage
)
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Union


class LoggingModelClientWrapper:
    """
    Wrapper that intercepts all model_client calls and records them.

    Usage:
        original_client = OpenAIChatCompletionClient(...)
        wrapped_client = LoggingModelClientWrapper(original_client, json_logger)
        agent = AssistantAgent(model_client=wrapped_client, ...)
    """

    def __init__(self, wrapped_client: ChatCompletionClient, json_logger, agent_name: str = "Unknown"):
        """
        Args:
            wrapped_client: The real client (OpenAIChatCompletionClient)
            json_logger: JSONLogger instance
            agent_name: Agent name (for logging)
        """
        self._wrapped = wrapped_client
        self._json_logger = json_logger
        self._agent_name = agent_name
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🔧 LoggingModelClientWrapper initialized for agent: {agent_name}")

    async def create(
            self,
            messages: Sequence[LLMMessage],
            **kwargs
    ) -> CreateResult:
        """
        Intercepts the create() method and records input/output

        Accepts any arguments the wrapped client may need
        (tools, json_output, extra_create_args, cancellation_token, tool_choice, etc.)

        IMPORTANT: For DeepSeek Reasoner, preserves the reasoning_content field
        in assistant messages as required by the API.
        """
        # Preserve reasoning_content in assistant messages for DeepSeek Reasoner
        # According to documentation: https://api-docs.deepseek.com/guides/thinking_mode#tool-calls
        processed_messages = self._preserve_reasoning_content(messages)

        # Extract message content for logging
        input_messages = []
        for msg in processed_messages:
            msg_dict = {
                "role": self._get_role(msg),
                "content": self._get_content(msg)
            }
            # Include reasoning_content if it exists (for DeepSeek Reasoner)
            if hasattr(msg, 'reasoning_content') and msg.reasoning_content:
                msg_dict["reasoning_content"] = msg.reasoning_content
            input_messages.append(msg_dict)

        # Log: LLM call started
        self.logger.info(f"🤖 LLM call started: {self._agent_name}, {len(processed_messages)} messages")

        start_time = datetime.now()

        try:
            # Call the real client with processed messages + all kwargs
            result = await self._wrapped.create(
                messages=processed_messages,
                **kwargs
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Extract response and reasoning_content (for DeepSeek Reasoner)
            response_content = result.content if hasattr(result, 'content') else str(result)
            reasoning_content = getattr(result, 'reasoning_content', None)

            # Extract token usage
            tokens_used = None
            if hasattr(result, 'usage') and result.usage:
                tokens_used = {
                    "prompt_tokens": result.usage.prompt_tokens if hasattr(result.usage, 'prompt_tokens') else 0,
                    "completion_tokens": result.usage.completion_tokens if hasattr(result.usage,
                                                                                   'completion_tokens') else 0,
                    "total_tokens": (result.usage.prompt_tokens + result.usage.completion_tokens) if hasattr(
                        result.usage, 'prompt_tokens') else 0
                }

            # Record in JSONLogger
            if self._json_logger:
                model_name = self._wrapped.model if hasattr(self._wrapped, 'model') else "unknown"

                # Add timing and model information
                llm_call_data = {
                    "timestamp": start_time.isoformat(),
                    "event_type": "llm_call",
                    "agent_name": self._agent_name,
                    "model": model_name,
                    "duration_seconds": duration,
                    "input_messages": input_messages,
                    "response": response_content,
                    "tokens_used": tokens_used or {}
                }

                # Add reasoning_content if it exists (DeepSeek Reasoner)
                if reasoning_content:
                    llm_call_data["reasoning_content"] = reasoning_content
                    self.logger.debug(f"💭 Reasoning content captured: {len(reasoning_content)} chars")

                # Add to events manually (more direct than using log_llm_call)
                self._json_logger.events.append(llm_call_data)

                self.logger.info(
                    f"✅ LLM call logged: {self._agent_name}, {duration:.2f}s, tokens={tokens_used.get('total_tokens', 0) if tokens_used else 0}")

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Record error
            if self._json_logger:
                self._json_logger.log_error(e, context=f"LLM call failed for {self._agent_name}")

            self.logger.error(f"❌ LLM call failed: {self._agent_name}, {duration:.2f}s, error: {e}")
            raise

    def _get_role(self, message: LLMMessage) -> str:
        """Extracts the message role"""
        if isinstance(message, SystemMessage):
            return "system"
        elif isinstance(message, UserMessage):
            return "user"
        elif isinstance(message, AssistantMessage):
            return "assistant"
        elif isinstance(message, FunctionExecutionResultMessage):
            return "function"
        else:
            return "unknown"

    def _get_content(self, message: LLMMessage) -> str:
        """Extracts the message content"""
        if hasattr(message, 'content'):
            content = message.content
            # If it's a list (FunctionCall), convert to string
            if isinstance(content, list):
                return str(content)
            return content
        return str(message)

    def _preserve_reasoning_content(self, messages: Sequence[LLMMessage]) -> Sequence[LLMMessage]:
        """
        Preserves the reasoning_content field in assistant messages.

        This is critical for DeepSeek Reasoner when using tool calls.
        According to official DeepSeek documentation:
        https://api-docs.deepseek.com/guides/thinking_mode#tool-calls

        The reasoning_content field must be included in assistant messages
        when continuing a conversation after tool calls.

        Args:
            messages: Sequence of LLM messages

        Returns:
            Sequence of messages with reasoning_content preserved
        """
        # Messages already come with reasoning_content if AutoGen preserved it
        # This method is mainly to ensure it doesn't get lost
        # and for logging/debugging

        processed = []
        for msg in messages:
            processed.append(msg)

            # Log if we find reasoning_content
            if isinstance(msg, AssistantMessage) and hasattr(msg, 'reasoning_content'):
                if msg.reasoning_content:
                    self.logger.info(
                        f"💭 Preserving reasoning_content in assistant message: {len(msg.reasoning_content)} chars")

        return processed

    def set_agent_name(self, agent_name: str):
        """
        Updates the agent name for logging

        Args:
            agent_name: New agent name
        """
        old_name = self._agent_name
        self._agent_name = agent_name
        self.logger.info(f"🔄 Agent name updated: {old_name} → {agent_name}")

    # Delegate all other attributes to the wrapped client
    def __getattr__(self, name):
        """Delegate attributes not found to the original client"""
        return getattr(self._wrapped, name)
