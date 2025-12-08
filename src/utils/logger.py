"""
Logging system for DaveAgent
Provides detailed logging with levels and colors
Logs are saved in .daveagent/logs/
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from typing import Optional


class DaveAgentLogger:
    """Custom logger for DaveAgent with color and file support"""

    def __init__(self, name: str = "DaveAgent", log_file: Optional[str] = None, level: int = logging.DEBUG):
        """
        Initialize the logger

        Args:
            name: Logger name
            log_file: Path to log file (optional, defaults to .daveagent/logs/)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()  # Clear existing handlers

        self.console = Console(stderr=True)

        # Handler para consola con colores (usando Rich)
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Handler para archivo (si se especifica o usar default)
        if log_file is None:
            # Default: .daveagent/logs/daveagent_YYYYMMDD_HHMMSS.log
            log_dir = Path(".daveagent") / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = str(log_dir / f"daveagent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # Siempre DEBUG en archivo
            file_formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log mensaje de debug"""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log mensaje informativo"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log advertencia"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error"""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log error crítico"""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log excepción con traceback"""
        self.logger.exception(message, extra=kwargs)

    def log_api_call(self, endpoint: str, params: dict):
        """Log llamada a API"""
        self.debug(f"🌐 API Call: {endpoint}")
        self.debug(f"   Params: {params}")

    def log_api_response(self, endpoint: str, status: str, data: any = None):
        """Log respuesta de API"""
        self.debug(f"✅ API Response: {endpoint} - {status}")
        if data:
            self.debug(f"   Data: {str(data)[:200]}...")

    def log_agent_selection(self, selected_agent: str, reason: str = ""):
        """Log selección de agente"""
        self.info(f"🤖 Agente seleccionado: {selected_agent}")
        if reason:
            self.debug(f"   Razón: {reason}")

    def log_task_start(self, task_id: int, task_title: str):
        """Log inicio de tarea"""
        self.info(f"▶️  Iniciando tarea {task_id}: {task_title}")

    def log_task_complete(self, task_id: int, success: bool):
        """Log finalización de tarea"""
        status = "✅ Completada" if success else "❌ Fallida"
        self.info(f"{status} - Tarea {task_id}")

    def log_message_processing(self, message_type: str, source: str, content_preview: str):
        """Log procesamiento de mensaje"""
        self.debug(f"📨 Procesando mensaje:")
        self.debug(f"   Tipo: {message_type}")
        self.debug(f"   Fuente: {source}")
        self.debug(f"   Contenido: {content_preview[:100]}...")

    def log_error_with_context(self, error: Exception, context: str):
        """Log error con contexto"""
        self.error(f"💥 Error en {context}")
        self.error(f"   Tipo: {type(error).__name__}")
        self.error(f"   Mensaje: {str(error)}")
        self.exception(f"   Traceback completo:")


# Instancia global del logger
_global_logger: Optional[DaveAgentLogger] = None


def get_logger(log_file: Optional[str] = None, level: int = logging.DEBUG) -> DaveAgentLogger:
    """
    Gets the global logger instance

    Args:
        log_file: Path to log file (only used on first call)
        level: Logging level

    Returns:
        DaveAgentLogger: Logger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = DaveAgentLogger(
            name="DaveAgent",
            log_file=log_file,
            level=level
        )

    return _global_logger


def set_log_level(level: int):
    """
    Changes the logging level

    Args:
        level: New level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = get_logger()
    logger.logger.setLevel(level)
    for handler in logger.logger.handlers:
        if isinstance(handler, RichHandler):
            handler.setLevel(level)


# Mantener compatibilidad con código antiguo
CodeAgentLogger = DaveAgentLogger
