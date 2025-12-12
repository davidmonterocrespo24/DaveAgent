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
from typing import Optional, Any


class DaveAgentLogger:
    """Custom logger for DaveAgent with color and file support"""

    def __init__(
        self, name: str = "DaveAgent", log_file: Optional[str] = None, level: int = logging.DEBUG
    ):
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

        # Silenciar loggers de terceros para evitar spam
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("autogen_core").setLevel(logging.WARNING)
        logging.getLogger("autogen_core.events").setLevel(logging.WARNING)
        #logging.getLogger("chromadb").setLevel(logging.WARNING)
        #logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
        #logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
        
        self.console = Console(stderr=True)

        # Console handler with colors (using Rich)
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setLevel(level)
        console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (if specified or use default)
        if log_file is None:
            # Default: .daveagent/logs/daveagent_YYYYMMDD_HHMMSS.log
            log_dir = Path(".daveagent") / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = str(log_dir / f"daveagent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # Always DEBUG in file
            file_formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log informational message"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error"""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical error"""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)

    def log_api_call(self, endpoint: str, params: dict):
        """Log API call"""
        self.debug(f"🌐 API Call: {endpoint}")
        self.debug(f"   Params: {params}")

    def log_api_response(self, endpoint: str, status: str, data: Any = None):
        """Log API response"""
        self.debug(f"✅ API Response: {endpoint} - {status}")
        if data:
            self.debug(f"   Data: {str(data)[:200]}...")

    def log_agent_selection(self, selected_agent: str, reason: str = ""):
        """Log agent selection"""
        self.info(f"🤖 Agent selected: {selected_agent}")
        if reason:
            self.debug(f"   Reason: {reason}")

    def log_task_start(self, task_id: int, task_title: str):
        """Log task start"""
        self.info(f"▶️  Starting task {task_id}: {task_title}")

    def log_task_complete(self, task_id: int, success: bool):
        """Log task completion"""
        status = "✅ Completed" if success else "❌ Failed"
        self.info(f"{status} - Task {task_id}")

    def log_message_processing(self, message_type: str, source: str, content_preview: str):
        """Log message processing"""
        self.debug(f"📨 Processing message:")
        self.debug(f"   Type: {message_type}")
        self.debug(f"   Source: {source}")
        self.debug(f"   Content: {content_preview[:100]}...")

    def log_error_with_context(self, error: Exception, context: str):
        """Log error with context"""
        self.error(f"💥 Error in {context}")
        self.error(f"   Type: {type(error).__name__}")
        self.error(f"   Message: {str(error)}")
        self.exception(f"   Full traceback:")


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
        _global_logger = DaveAgentLogger(name="DaveAgent", log_file=log_file, level=level)

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


# Maintain compatibility with old code
CodeAgentLogger = DaveAgentLogger
