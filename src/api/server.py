"""
FastAPI WebSocket Server - API sin UI
Solo envía eventos JSON estructurados al frontend React

El backend NO renderiza UI - solo procesa lógica y emite eventos.
El frontend React renderiza toda la interfaz.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.event_emitter import EventEmitter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="DaveAgent API",
    description="API backend for DaveAgent Web Interface",
    version="1.2.1",
)

# CORS para desarrollo (permitir frontend en localhost:5173 y :3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================================
# REST ENDPOINTS - Para datos estáticos
# =========================================================================


@app.get("/")
async def root():
    """Root endpoint - Información de la API"""
    return {
        "name": "DaveAgent API",
        "version": "1.2.1",
        "endpoints": {
            "websocket": "/ws/agent",
            "health": "/api/health",
            "sessions": "/api/sessions",
            "files": "/api/files",
        },
    }


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.2.1",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/sessions")
async def list_sessions():
    """
    Lista todas las sesiones guardadas

    TODO: Implementar sin crear instancia completa de AgentOrchestrator
    Por ahora retorna lista vacía
    """
    try:
        # Importar StateManager directamente
        from src.managers.state_manager import StateManager

        state_manager = StateManager()
        sessions = state_manager.list_sessions()

        return {
            "sessions": sessions,
            "total": len(sessions),
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return {"sessions": [], "total": 0, "error": str(e)}


@app.get("/api/files")
async def list_files(path: str = "."):
    """
    Lista archivos del proyecto

    Args:
        path: Ruta relativa a listar (default: directorio actual)

    Returns:
        JSON con lista de archivos y directorios
    """
    try:
        base_path = Path(path).resolve()

        # Verificar que existe
        if not base_path.exists():
            return JSONResponse(
                status_code=404, content={"error": "Path not found", "path": str(base_path)}
            )

        # Verificar que no se escape del proyecto
        cwd = Path.cwd()
        if not str(base_path).startswith(str(cwd)):
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied - path outside project", "path": str(base_path)},
            )

        files = []
        for item in sorted(base_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
            # Skip hidden files y directorios especiales
            if item.name.startswith("."):
                continue
            if item.name in ["__pycache__", "node_modules", "venv", ".venv"]:
                continue

            files.append(
                {
                    "name": item.name,
                    "path": str(item.relative_to(cwd)),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                }
            )

        return {
            "files": files,
            "path": str(base_path.relative_to(cwd)),
            "total": len(files),
        }

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# =========================================================================
# WEBSOCKET ENDPOINT - Conexión principal con agente
# =========================================================================


@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """
    WebSocket principal - Conexión bidireccional con el agente

    Protocolo:
        Cliente → Servidor:
            { "command": "execute", "content": "user message or /command" }
            { "command": "list_sessions" }

        Servidor → Cliente:
            { "type": "connected", "version": "1.2.1", "timestamp": "..." }
            { "type": "agent_message", "agent": "Coder", "content": "...", "timestamp": "..." }
            { "type": "thinking", "agent": "Planner", "content": "...", "timestamp": "..." }
            { "type": "tool_call", "agent": "Coder", "tool_name": "write_file", ... }
            { "type": "error", "message": "...", "timestamp": "..." }
            ... etc (ver event_emitter.py)
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    # Crear event emitter que enviará eventos al WebSocket
    async def send_event(data: str):
        """Callback para enviar eventos JSON al cliente"""
        try:
            await websocket.send_text(data)
        except Exception as e:
            logger.error(f"Error sending event: {e}")

    event_emitter = EventEmitter(send_event)

    # Variable para el agente (se crea bajo demanda)
    agent = None

    try:
        # Enviar evento de conexión inicial
        await event_emitter.emit_connected(version="1.2.1", session_id=None)

        logger.info("WebSocket ready - waiting for messages")

        # Loop principal - Procesar mensajes del cliente
        while True:
            # Recibir mensaje del frontend
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                command = message.get("command", "")
                content = message.get("content", "")

                logger.info(f"Received command: {command}, content: {content[:50]}...")

                # =====================================================
                # COMANDO: execute - Ejecutar user input
                # =====================================================
                if command == "execute":
                    # Lazy initialization del agente (solo cuando se necesita)
                    if agent is None:
                        logger.info("Initializing DaveAgent...")
                        await event_emitter.emit_info("Initializing agent...")

                        # Importar y crear agente
                        from src.main import DaveAgentCLI

                        agent = DaveAgentCLI(debug=False, headless=True)

                        # Reemplazar CLI interface con event emitter
                        agent.cli = event_emitter

                        logger.info("DaveAgent initialized")
                        await event_emitter.emit_success("Agent ready")

                    # Procesar comando o mensaje
                    if content.startswith("/"):
                        # Es un comando interno (/help, /exit, etc.)
                        logger.info(f"Processing command: {content}")
                        should_continue = await agent.handle_command(content)

                        if not should_continue:
                            # Usuario pidió salir
                            await event_emitter.emit_info("Session closed")
                            break
                    else:
                        # Es un mensaje normal para el agente
                        logger.info(f"Processing user request: {content[:100]}...")
                        await agent.process_user_request(content)

                # =====================================================
                # COMANDO: list_sessions - Listar sesiones
                # =====================================================
                elif command == "list_sessions":
                    logger.info("Listing sessions")

                    if agent and agent.state_manager:
                        sessions = agent.state_manager.list_sessions()
                    else:
                        # Si no hay agente, crear StateManager temporal
                        from src.managers.state_manager import StateManager

                        temp_manager = StateManager()
                        sessions = temp_manager.list_sessions()

                    await websocket.send_json(
                        {
                            "type": "sessions_list",
                            "sessions": sessions,
                            "total": len(sessions),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                # =====================================================
                # COMANDO: load_session - Cargar sesión
                # =====================================================
                elif command == "load_session":
                    session_id = content
                    logger.info(f"Loading session: {session_id}")

                    if agent is None:
                        await event_emitter.emit_error(
                            "Agent not initialized - send a message first"
                        )
                    else:
                        # Usar el comando existente
                        await agent.handle_command(f"/load-session {session_id}")

                # =====================================================
                # COMANDO desconocido
                # =====================================================
                else:
                    logger.warning(f"Unknown command: {command}")
                    await event_emitter.emit_error(f"Unknown command: {command}")

            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await event_emitter.emit_error("Invalid JSON message")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await event_emitter.emit_error(str(e), context="message_handler")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await event_emitter.emit_error(str(e), context="websocket")
        except:
            pass

    finally:
        # Cleanup
        if agent:
            try:
                logger.info("Closing agent...")
                await agent.state_manager.close()
                logger.info("Agent closed successfully")
            except Exception as e:
                logger.error(f"Error closing agent: {e}")

        logger.info("WebSocket connection closed")


# =========================================================================
# STARTUP/SHUTDOWN EVENTS
# =========================================================================


@app.on_event("startup")
async def startup_event():
    """Evento de inicio del servidor"""
    logger.info("=" * 70)
    logger.info("🚀 DaveAgent API Server Starting")
    logger.info("=" * 70)
    logger.info("📡 WebSocket endpoint: /ws/agent")
    logger.info("🌐 REST API: /api/*")
    logger.info("🔧 Health check: /api/health")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre del servidor"""
    logger.info("🔚 DaveAgent API Server Shutting Down")


# =========================================================================
# ERROR HANDLERS
# =========================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para excepciones no capturadas"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# =========================================================================
# MAIN - Para ejecutar directamente
# =========================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info",
    )
