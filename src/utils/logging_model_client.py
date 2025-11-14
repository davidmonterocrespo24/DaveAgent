"""
Logging Model Client Wrapper - Intercepta llamadas al LLM para logging

Este wrapper se coloca alrededor del model_client real y captura:
- Mensajes enviados al LLM (input)
- Respuestas recibidas del LLM (output)
- Uso de tokens
- Timing

Lo registra todo en el JSONLogger para trazabilidad completa.
"""
import logging
from typing import Any, Dict, List, Optional, Sequence, Union
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


class LoggingModelClientWrapper:
    """
    Wrapper que intercepta todas las llamadas al model_client y las registra.

    Se usa así:
        original_client = OpenAIChatCompletionClient(...)
        wrapped_client = LoggingModelClientWrapper(original_client, json_logger)
        agent = AssistantAgent(model_client=wrapped_client, ...)
    """

    def __init__(self, wrapped_client: ChatCompletionClient, json_logger, agent_name: str = "Unknown"):
        """
        Args:
            wrapped_client: El cliente real (OpenAIChatCompletionClient)
            json_logger: Instancia de JSONLogger
            agent_name: Nombre del agente (para logging)
        """
        self._wrapped = wrapped_client
        self._json_logger = json_logger
        self._agent_name = agent_name
        self.logger = logging.getLogger(__name__)

    async def create(
        self,
        messages: Sequence[LLMMessage],
        **kwargs
    ) -> CreateResult:
        """
        Intercepta el método create() y registra entrada/salida

        Acepta cualquier argumento que el cliente wrapped pueda necesitar
        (tools, json_output, extra_create_args, cancellation_token, tool_choice, etc.)
        """
        # Extraer contenido de los mensajes para logging
        input_messages = []
        for msg in messages:
            msg_dict = {
                "role": self._get_role(msg),
                "content": self._get_content(msg)
            }
            input_messages.append(msg_dict)

        # Log: Llamada a LLM iniciada
        self.logger.debug(f"🤖 LLM call started: {self._agent_name}, {len(messages)} messages")

        start_time = datetime.now()

        try:
            # Llamar al cliente real con TODOS los kwargs
            result = await self._wrapped.create(
                messages=messages,
                **kwargs
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Extraer respuesta
            response_content = result.content if hasattr(result, 'content') else str(result)

            # Extraer uso de tokens
            tokens_used = None
            if hasattr(result, 'usage') and result.usage:
                tokens_used = {
                    "prompt_tokens": result.usage.prompt_tokens if hasattr(result.usage, 'prompt_tokens') else 0,
                    "completion_tokens": result.usage.completion_tokens if hasattr(result.usage, 'completion_tokens') else 0,
                    "total_tokens": (result.usage.prompt_tokens + result.usage.completion_tokens) if hasattr(result.usage, 'prompt_tokens') else 0
                }

            # Registrar en JSONLogger
            if self._json_logger:
                model_name = self._wrapped.model if hasattr(self._wrapped, 'model') else "unknown"

                # Agregar información de timing y modelo
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

                # Agregar a eventos manualmente (más directo que usar log_llm_call)
                self._json_logger.events.append(llm_call_data)

                self.logger.debug(f"✅ LLM call logged: {self._agent_name}, {duration:.2f}s, {tokens_used}")

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Registrar error
            if self._json_logger:
                self._json_logger.log_error(e, context=f"LLM call failed for {self._agent_name}")

            self.logger.error(f"❌ LLM call failed: {self._agent_name}, {duration:.2f}s, error: {e}")
            raise

    def _get_role(self, message: LLMMessage) -> str:
        """Extrae el rol del mensaje"""
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
        """Extrae el contenido del mensaje"""
        if hasattr(message, 'content'):
            content = message.content
            # Si es una lista (FunctionCall), convertir a string
            if isinstance(content, list):
                return str(content)
            return content
        return str(message)

    # Delegar todos los demás atributos al cliente wrapped
    def __getattr__(self, name):
        """Delegar atributos no encontrados al cliente original"""
        return getattr(self._wrapped, name)
