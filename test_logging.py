"""
Script de prueba para verificar que el sistema de logging funciona correctamente
"""
import asyncio
from src.utils import get_logger
import logging
import sys

# Configurar codificación UTF-8 para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


async def test_logging():
    """Prueba el sistema de logging"""

    print("=" * 60)
    print("PRUEBA DEL SISTEMA DE LOGGING")
    print("=" * 60)

    # 1. Crear logger con archivo
    logger = get_logger(log_file="logs/test_logging.log", level=logging.DEBUG)

    print("\nLogger creado exitosamente")

    # 2. Probar diferentes niveles
    print("\nProbando diferentes niveles de logging...")

    logger.debug("Este es un mensaje DEBUG")
    logger.info("Este es un mensaje INFO")
    logger.warning("Este es un mensaje WARNING")
    logger.error("Este es un mensaje ERROR")
    logger.critical("Este es un mensaje CRITICAL")

    # 3. Probar métodos especializados
    print("\nProbando métodos especializados...")

    logger.log_agent_selection("Coder", "Tarea simple detectada")
    logger.log_task_start(1, "Crear función de multiplicación")
    logger.log_task_complete(1, True)

    # 4. Probar logging de API
    logger.log_api_call("https://api.deepseek.com/v1/chat/completions", {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "test"}]
    })

    logger.log_api_response("https://api.deepseek.com/v1/chat/completions", "200 OK", "Response data")

    # 5. Probar logging de mensajes
    logger.log_message_processing("TextMessage", "Coder", "He creado la función multiplicar...")

    # 6. Probar logging de errores
    try:
        raise ValueError("Este es un error de prueba")
    except Exception as e:
        logger.log_error_with_context(e, "test_logging")

    print("\nTodas las pruebas de logging completadas")
    print("\nRevisa el archivo: logs/test_logging.log")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_logging())
