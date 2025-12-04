"""
Configuración para usar DeepSeek Reasoner (R1) con thinking mode

SOLUCIÓN IMPLEMENTADA:
Usar DeepSeekReasoningClient que wrappea OpenAIChatCompletionClient
para manejar correctamente el campo reasoning_content requerido por DeepSeek R1.

El cliente:
1. Habilita thinking mode automáticamente para deepseek-reasoner
2. Inyecta extra_body={"thinking": {"type": "enabled"}} cuando es necesario
3. Cachea reasoning_content para preservarlo en tool calls

Basado en:
- https://api-docs.deepseek.com/guides/thinking_mode
- https://docs.ag2.ai/docs/api/autogen_ext.models.openai
"""

def should_use_reasoning_client(settings):
    """
    Determina si debemos usar DeepSeekReasoningClient para este modelo.

    Args:
        settings: Objeto de configuración con model attribute

    Returns:
        bool: True si debemos usar el cliente de razonamiento
    """
    # Usar reasoning client para deepseek-reasoner o deepseek-chat
    return settings.model in ("deepseek-reasoner", "deepseek-chat", "deepseek-r1")


def get_thinking_mode_enabled(model: str) -> bool:
    """
    Determina si thinking mode debe estar habilitado para este modelo.

    Args:
        model: Nombre del modelo

    Returns:
        bool: True si thinking mode debe estar habilitado
    """
    # Habilitar automáticamente para deepseek-reasoner y deepseek-r1
    return model in ("deepseek-reasoner", "deepseek-r1")


# Documentación para el usuario
DEEPSEEK_REASONER_INFO = """
═══════════════════════════════════════════════════════════════
🧠 DEEPSEEK REASONER (R1) - THINKING MODE ENABLED

Este cliente usa DeepSeek R1 con modo de razonamiento extendido.

CARACTERÍSTICAS:
✅ Modo de razonamiento (thinking mode) habilitado
✅ Soporte completo para tool calls
✅ Preservación automática de reasoning_content
✅ Compatible con todas las funciones de AutoGen

MODELOS SOPORTADOS:
- deepseek-reasoner (R1) - Recomendado
- deepseek-chat + thinking mode
- deepseek-r1

FUNCIONAMIENTO:
El modelo genera un "reasoning_content" con su proceso de
razonamiento antes de dar la respuesta final. Este razonamiento
mejora la calidad de las respuestas, especialmente en tareas
complejas y con múltiples tool calls.

REFERENCIA:
https://api-docs.deepseek.com/guides/thinking_mode
═══════════════════════════════════════════════════════════════
"""
