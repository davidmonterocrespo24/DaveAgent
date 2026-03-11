"""
EventEmitter - Sistema de eventos para WebSocket
Reemplaza CLIInterface para emitir eventos JSON en vez de print()

Este módulo permite que el backend Python envíe eventos estructurados
al frontend React sin tener que formatear la UI en el backend.
"""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


class EventEmitter:
    """
    Emite eventos estructurados en formato JSON para el frontend.

    Reemplaza CLIInterface manteniendo la misma API pero enviando
    eventos JSON vía WebSocket en vez de imprimir en terminal.

    Todos los métodos de formato/UI están delegados al frontend React.
    """

    def __init__(self, send_callback: Callable[[str], None]):
        """
        Inicializa el EventEmitter

        Args:
            send_callback: Función async para enviar JSON al WebSocket
                          Debe aceptar un string (JSON serializado)
        """
        self.send = send_callback
        self.mentioned_files: List[str] = []
        self.current_mode = "agent"

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Envía un evento JSON estructurado al frontend

        Args:
            event_type: Tipo de evento (agent_message, thinking, tool_call, etc.)
            data: Datos del evento
        """
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }
        await self.send(json.dumps(event))

    # =========================================================================
    # EVENTOS ESPECÍFICOS - Para cada tipo de mensaje
    # =========================================================================

    async def emit_connected(self, version: str, session_id: Optional[str] = None):
        """Evento: Conexión establecida"""
        await self.emit(
            "connected",
            {
                "version": version,
                "session_id": session_id,
            },
        )

    async def emit_agent_message(self, agent: str, content: str):
        """Evento: Mensaje de un agente"""
        await self.emit(
            "agent_message",
            {
                "agent": agent,
                "content": content,
            },
        )

    async def emit_thinking(self, agent: str, content: str):
        """Evento: Agente está pensando/razonando"""
        await self.emit(
            "thinking",
            {
                "agent": agent,
                "content": content,
            },
        )

    async def emit_tool_call(self, agent: str, tool_name: str, tool_args: Dict[str, Any]):
        """Evento: Agente está llamando a una herramienta"""
        await self.emit(
            "tool_call",
            {
                "agent": agent,
                "tool_name": tool_name,
                "tool_args": tool_args,
            },
        )

    async def emit_tool_result(
        self, agent: str, tool_name: str, result: str, success: bool = True
    ):
        """Evento: Resultado de ejecución de herramienta"""
        await self.emit(
            "tool_result",
            {
                "agent": agent,
                "tool_name": tool_name,
                "result": result,
                "success": success,
            },
        )

    async def emit_error(self, message: str, context: Optional[str] = None):
        """Evento: Error ocurrido"""
        await self.emit(
            "error",
            {
                "message": message,
                "context": context,
            },
        )

    async def emit_success(self, message: str):
        """Evento: Operación exitosa"""
        await self.emit("success", {"message": message})

    async def emit_info(self, message: str, prefix: Optional[str] = None):
        """Evento: Mensaje informativo"""
        await self.emit(
            "info",
            {
                "message": message,
                "prefix": prefix,
            },
        )

    async def emit_warning(self, message: str):
        """Evento: Advertencia"""
        await self.emit("warning", {"message": message})

    async def emit_session(
        self, action: str, session_id: str, metadata: Optional[Dict] = None
    ):
        """Evento: Cambio de sesión (loaded, saved, created)"""
        await self.emit(
            "session",
            {
                "action": action,
                "session_id": session_id,
                "metadata": metadata or {},
            },
        )

    async def emit_code(
        self, code: str, filename: Optional[str] = None, language: Optional[str] = None
    ):
        """Evento: Mostrar código con syntax highlighting"""
        await self.emit(
            "code",
            {
                "code": code,
                "filename": filename,
                "language": language,
            },
        )

    async def emit_diff(self, diff_text: str, filename: Optional[str] = None):
        """Evento: Mostrar diff de cambios"""
        await self.emit(
            "diff",
            {
                "diff": diff_text,
                "filename": filename,
            },
        )

    # =========================================================================
    # MÉTODOS DE COMPATIBILIDAD CON CLIInterface
    # =========================================================================
    # Mantienen la misma API que CLIInterface para no romper código existente

    async def print_banner(self):
        """Envía evento para mostrar banner - El frontend renderiza el ASCII art"""
        await self.emit("banner", {})

    async def print_user_message(self, message: str):
        """Imprime mensaje del usuario"""
        await self.emit(
            "user_message",
            {
                "content": message,
            },
        )

    async def print_agent_message(self, content: str, agent_name: str = "Agent"):
        """Imprime mensaje de agente"""
        await self.emit_agent_message(agent_name, content)

    async def print_thinking(self, message: str, agent: str = "System"):
        """Imprime mensaje de pensamiento"""
        await self.emit_thinking(agent, message)

    async def print_success(self, message: str):
        """Imprime mensaje de éxito"""
        await self.emit_success(message)

    async def print_error(self, message: str):
        """Imprime mensaje de error"""
        await self.emit_error(message)

    async def print_info(self, message: str, prefix: Optional[str] = None):
        """Imprime mensaje informativo"""
        await self.emit_info(message, prefix)

    async def print_warning(self, message: str):
        """Imprime advertencia"""
        await self.emit_warning(message)

    async def print_code(self, code: str, filename: str = None, max_lines: int = None):
        """
        Imprime código con syntax highlighting

        Args:
            code: Código a mostrar
            filename: Nombre del archivo (para detectar lenguaje)
            max_lines: Límite de líneas (ignorado, frontend decide)
        """
        # Detectar lenguaje del filename
        language = None
        if filename:
            ext = filename.split(".")[-1] if "." in filename else None
            lang_map = {
                "py": "python",
                "js": "javascript",
                "ts": "typescript",
                "tsx": "typescript",
                "jsx": "javascript",
                "json": "json",
                "md": "markdown",
                "yaml": "yaml",
                "yml": "yaml",
                "toml": "toml",
                "sh": "bash",
                "bash": "bash",
            }
            language = lang_map.get(ext, ext)

        await self.emit_code(code, filename, language)

    async def print_diff(self, diff_text: str):
        """Imprime diff con colores"""
        await self.emit_diff(diff_text)

    async def print_mentioned_files(self):
        """Imprime archivos mencionados con @"""
        if self.mentioned_files:
            await self.emit_info(
                f"Mentioned files: {', '.join(self.mentioned_files)}", prefix="Files"
            )

    def get_mentioned_files_content(self) -> str:
        """
        Obtiene el contenido de archivos mencionados
        NOTA: En modo API, esto debería hacerse diferente
        """
        # TODO: Implementar lectura de archivos para API mode
        return ""

    def start_thinking(self, message: str = "thinking"):
        """
        Inicia animación de "pensando"
        En modo API, no hace nada - el frontend maneja spinners
        """
        pass

    def stop_thinking(self, clear: bool = True):
        """
        Detiene animación de "pensando"
        En modo API, no hace nada
        """
        pass

    def clear_screen(self):
        """
        Limpia la pantalla
        En modo API, envía evento para que frontend limpie
        """
        # Crear tarea async para emit
        import asyncio

        asyncio.create_task(self.emit("clear_screen", {}))

    def set_mode(self, mode: str):
        """Cambia el modo actual (agent/chat)"""
        self.current_mode = mode
        # Enviar evento de cambio de modo
        import asyncio

        asyncio.create_task(
            self.emit(
                "mode_change",
                {
                    "mode": mode,
                },
            )
        )

    async def print_goodbye(self):
        """Mensaje de despedida"""
        await self.emit("goodbye", {})

    async def print_help(self):
        """
        Muestra ayuda de comandos
        Envía estructura de comandos para que frontend renderice
        """
        help_data = {
            "sections": [
                {
                    "title": "CONVERSATION",
                    "icon": "💬",
                    "commands": [
                        {"cmd": "/help", "desc": "Show this help"},
                        {"cmd": "/clear", "desc": "Clear screen"},
                        {"cmd": "/new", "desc": "Start new conversation"},
                        {"cmd": "/exit, /quit", "desc": "Exit DaveAgent"},
                    ],
                },
                {
                    "title": "SEARCH & MEMORY",
                    "icon": "🔍",
                    "commands": [
                        {"cmd": "/search <query>", "desc": "Search code and analyze"},
                        {"cmd": "/index", "desc": "Index project in vector memory"},
                        {"cmd": "/memory", "desc": "Show memory statistics"},
                    ],
                },
                {
                    "title": "FILES",
                    "icon": "📁",
                    "commands": [
                        {"cmd": "@<filename>", "desc": "Mention file with high priority"},
                    ],
                },
                {
                    "title": "SESSION MANAGEMENT",
                    "icon": "📊",
                    "commands": [
                        {"cmd": "/new-session <title>", "desc": "Create new session"},
                        {"cmd": "/save-session [title]", "desc": "Save current session"},
                        {"cmd": "/load-session [id]", "desc": "Load session"},
                        {"cmd": "/sessions", "desc": "List all sessions"},
                        {"cmd": "/history", "desc": "Show session history"},
                    ],
                },
                {
                    "title": "CONFIGURATION",
                    "icon": "⚙️",
                    "commands": [
                        {"cmd": "/config", "desc": "Show current configuration"},
                        {"cmd": "/set-model <model>", "desc": "Change model"},
                        {"cmd": "/modo-agent", "desc": "Enable agent mode (full tools)"},
                        {"cmd": "/modo-chat", "desc": "Enable chat mode (read-only)"},
                        {"cmd": "/debug", "desc": "Toggle debug mode"},
                        {"cmd": "/logs", "desc": "Show log file location"},
                    ],
                },
                {
                    "title": "SKILLS",
                    "icon": "🎯",
                    "commands": [
                        {"cmd": "/skills", "desc": "List available skills"},
                        {"cmd": "/skill-info <name>", "desc": "Show skill details"},
                    ],
                },
            ]
        }
        await self.emit("help", help_data)

    # =========================================================================
    # MÉTODOS ADICIONALES PARA COMPATIBILIDAD
    # =========================================================================

    async def get_user_input(self) -> str:
        """
        En modo API, el input viene del WebSocket, no de prompt
        Este método no debería llamarse
        """
        raise NotImplementedError("get_user_input not available in API mode")
