PLAN FINAL: Frontend React con UI Total / Backend Python API Puro
Ahora sí, arquitectura correcta con separación completa:
Backend Python: Solo envía eventos en JSON (sin formato, sin colores, sin UI)
Frontend React: Renderiza toda la UI (colores, banner, formato, terminal)
🏗️ ARQUITECTURA DEFINITIVA
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript)                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  UI Components (TODO EL RENDERING)                    │  │
│  │  - Terminal Component (xterm.js)                      │  │
│  │  - Banner Component (ASCII art)                       │  │
│  │  - Message Renderer (colores, markdown)               │  │
│  │  - Code Highlighter (syntax highlighting)             │  │
│  │  - Diff Viewer (git diffs)                            │  │
│  │  - Agent Status Indicator                             │  │
│  │  - Spinner/Loading Animation                          │  │
│  └───────────────────────────────────────────────────────┘  │
│               ▲ WebSocket (JSON Events)                     │
└───────────────┼─────────────────────────────────────────────┘
                │
                │ JSON Messages:
                │ { "type": "agent_message", "agent": "Coder", "content": "...", "timestamp": ... }
                │ { "type": "tool_call", "tool": "write_file", "args": {...} }
                │ { "type": "thinking", "agent": "Planner", "content": "..." }
                │ { "type": "error", "message": "..." }
                │
┌───────────────┼─────────────────────────────────────────────┐
│               ▼                                              │
│  BACKEND (Python - FastAPI)                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  API Layer (SIN UI - Solo Datos)                      │  │
│  │  - WebSocket: /ws/agent                               │  │
│  │  - REST: /api/sessions, /api/files, etc.              │  │
│  │  - Envía solo eventos JSON estructurados              │  │
│  └───────────────────────────────────────────────────────┘  │
│               │                                              │
│               ▼                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  DaveAgentCLI (Refactorizado)                         │  │
│  │  - Lógica de agentes (sin print/format)               │  │
│  │  - Emite eventos estructurados                        │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
📡 PROTOCOLO WebSocket (Backend → Frontend)
El backend solo envía eventos JSON, el frontend decide cómo renderizarlos.
Tipos de Eventos:
// Frontend types (types/events.ts)

type WebSocketEvent = 
  | ConnectedEvent
  | AgentMessageEvent
  | ThinkingEvent
  | ToolCallEvent
  | ToolResultEvent
  | ErrorEvent
  | SuccessEvent
  | InfoEvent
  | SessionEvent;

interface ConnectedEvent {
  type: 'connected';
  version: string;
  session_id?: string;
}

interface AgentMessageEvent {
  type: 'agent_message';
  agent: string;          // "Coder", "Planner", "CodeSearcher"
  content: string;        // Texto del mensaje
  timestamp: string;
}

interface ThinkingEvent {
  type: 'thinking';
  agent: string;
  content: string;
  timestamp: string;
}

interface ToolCallEvent {
  type: 'tool_call';
  agent: string;
  tool_name: string;
  tool_args: Record<string, any>;
  timestamp: string;
}

interface ToolResultEvent {
  type: 'tool_result';
  agent: string;
  tool_name: string;
  result: string;
  success: boolean;
  timestamp: string;
}

interface ErrorEvent {
  type: 'error';
  message: string;
  context?: string;
  timestamp: string;
}

interface SuccessEvent {
  type: 'success';
  message: string;
  timestamp: string;
}

interface InfoEvent {
  type: 'info';
  message: string;
  prefix?: string;
  timestamp: string;
}

interface SessionEvent {
  type: 'session';
  action: 'loaded' | 'saved' | 'created';
  session_id: string;
  metadata?: Record<string, any>;
}
📋 PLAN DE MIGRACIÓN (3 FASES)
FASE 1: Refactorizar Backend - API Sin UI (2 días)
1.1 Crear Event Emitter (src/api/event_emitter.py)
"""
EventEmitter - Sistema de eventos para WebSocket
Reemplaza CLIInterface para emitir eventos JSON en vez de print()
"""
from datetime import datetime
from typing import Any, Callable, Dict, Optional
import json

class EventEmitter:
    """Emite eventos estructurados en vez de print/format"""
    
    def __init__(self, send_callback: Callable[[str], None]):
        """
        Args:
            send_callback: Función async para enviar JSON al WebSocket
        """
        self.send = send_callback
        self.mentioned_files = []
        self.current_mode = "agent"
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Envía evento JSON al frontend"""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
        await self.send(json.dumps(event))
    
    async def emit_connected(self, version: str, session_id: Optional[str] = None):
        await self.emit("connected", {
            "version": version,
            "session_id": session_id
        })
    
    async def emit_agent_message(self, agent: str, content: str):
        await self.emit("agent_message", {
            "agent": agent,
            "content": content
        })
    
    async def emit_thinking(self, agent: str, content: str):
        await self.emit("thinking", {
            "agent": agent,
            "content": content
        })
    
    async def emit_tool_call(self, agent: str, tool_name: str, tool_args: Dict[str, Any]):
        await self.emit("tool_call", {
            "agent": agent,
            "tool_name": tool_name,
            "tool_args": tool_args
        })
    
    async def emit_tool_result(self, agent: str, tool_name: str, result: str, success: bool = True):
        await self.emit("tool_result", {
            "agent": agent,
            "tool_name": tool_name,
            "result": result,
            "success": success
        })
    
    async def emit_error(self, message: str, context: Optional[str] = None):
        await self.emit("error", {
            "message": message,
            "context": context
        })
    
    async def emit_success(self, message: str):
        await self.emit("success", {"message": message})
    
    async def emit_info(self, message: str, prefix: Optional[str] = None):
        await self.emit("info", {
            "message": message,
            "prefix": prefix
        })
    
    async def emit_session(self, action: str, session_id: str, metadata: Optional[Dict] = None):
        await self.emit("session", {
            "action": action,
            "session_id": session_id,
            "metadata": metadata or {}
        })
    
    # Métodos de compatibilidad con CLIInterface
    async def print_agent_message(self, content: str, agent_name: str = "Agent"):
        await self.emit_agent_message(agent_name, content)
    
    async def print_thinking(self, message: str):
        await self.emit_thinking("System", message)
    
    async def print_success(self, message: str):
        await self.emit_success(message)
    
    async def print_error(self, message: str):
        await self.emit_error(message)
    
    async def print_info(self, message: str, prefix: Optional[str] = None):
        await self.emit_info(message, prefix)
    
    def start_thinking(self, message: str = "thinking"):
        """No-op en modo API - el frontend maneja spinners"""
        pass
    
    def stop_thinking(self, clear: bool = True):
        """No-op en modo API"""
        pass
    
    def set_mode(self, mode: str):
        self.current_mode = mode
1.2 Crear WebSocket Server (src/api/server.py)
"""
FastAPI WebSocket Server - API sin UI
Solo envía eventos JSON estructurados
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime

from src.api.event_emitter import EventEmitter
from src.config.orchestrator import AgentOrchestrator

app = FastAPI(title="DaveAgent API")

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": "1.2.1"}

@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """
    WebSocket principal - Conexión con agente
    Envía solo eventos JSON estructurados
    """
    await websocket.accept()
    
    # Crear event emitter
    async def send_event(data: str):
        await websocket.send_text(data)
    
    event_emitter = EventEmitter(send_event)
    
    # Crear instancia del agente
    agent = AgentOrchestrator(
        debug=False,
        headless=True  # Sin CLI
    )
    
    # Reemplazar CLI con event emitter
    agent.cli = event_emitter
    
    try:
        # Enviar evento de conexión
        await event_emitter.emit_connected(
            version="1.2.1",
            session_id=agent.state_manager.session_id
        )
        
        # Loop principal
        while True:
            # Recibir mensaje del frontend
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                command = message.get("command", "")
                content = message.get("content", "")
                
                if command == "execute":
                    # Ejecutar comando del usuario
                    if content.startswith("/"):
                        should_continue = await agent.handle_command(content)
                        if not should_continue:
                            await event_emitter.emit_info("Session closed")
                            break
                    else:
                        # Procesar request normal
                        await agent.process_user_request(content)
                        
                elif command == "list_sessions":
                    # Listar sesiones
                    sessions = agent.state_manager.list_sessions()
                    await websocket.send_json({
                        "type": "sessions_list",
                        "sessions": sessions
                    })
                    
            except json.JSONDecodeError:
                await event_emitter.emit_error("Invalid JSON message")
            except Exception as e:
                await event_emitter.emit_error(str(e), context="message_handler")
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
        try:
            await event_emitter.emit_error(str(e))
        except:
            pass
    finally:
        try:
            await agent.state_manager.close()
        except:
            pass

# REST endpoints para datos estáticos
@app.get("/api/sessions")
async def list_sessions():
    """Lista todas las sesiones guardadas"""
    # TODO: Implementar sin crear instancia completa
    return {"sessions": []}

@app.get("/api/files")
async def list_files(path: str = "."):
    """Lista archivos del proyecto"""
    import os
    from pathlib import Path
    
    try:
        base_path = Path(path)
        files = []
        for item in base_path.iterdir():
            if item.name.startswith('.'):
                continue
            files.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0
            })
        return {"files": files, "path": str(base_path)}
    except Exception as e:
        return {"error": str(e)}
1.3 Adaptar src/main.py para emitir eventos
Modificar los métodos que hacen self.cli.print_* para usar el EventEmitter:
# En process_user_request(), cambiar:
# self.cli.print_thinking(f"💭 {agent_name}: {content}")
# Por:
await self.cli.emit_thinking(agent_name, content)

# self.cli.print_info(f"🔧 Calling tool: {tool_name}")
# Por:
await self.cli.emit_tool_call(agent_name, tool_name, tool_args)
FASE 2: Frontend React - UI Completa (3-4 días)
Estructura del Proyecto:
daveagent-web/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── components/
    │   ├── Terminal/
    │   │   ├── Terminal.tsx              # xterm.js wrapper
    │   │   ├── TerminalRenderer.tsx      # Renderiza eventos como líneas
    │   │   ├── MessageLine.tsx           # Renderiza un mensaje
    │   │   ├── CodeBlock.tsx             # Syntax highlighting
    │   │   ├── DiffViewer.tsx            # Git diffs
    │   │   └── Banner.tsx                # ASCII banner
    │   ├── Input/
    │   │   ├── CommandInput.tsx          # Input con @ autocomplete
    │   │   └── FileAutocomplete.tsx      # Autocomplete de archivos
    │   ├── Status/
    │   │   ├── AgentIndicator.tsx        # Indicador de agente activo
    │   │   └── LoadingSpinner.tsx        # Spinner customizado
    │   └── Session/
    │       └── SessionInfo.tsx           # Info de sesión actual
    ├── hooks/
    │   ├── useWebSocket.ts               # Gestión WebSocket
    │   ├── useTerminal.ts                # Estado del terminal
    │   └── useEventHandler.ts            # Procesa eventos
    ├── services/
    │   ├── websocket.service.ts          # Cliente WebSocket
    │   └── api.service.ts                # Cliente REST
    ├── types/
    │   ├── events.ts                     # Tipos de eventos
    │   └── terminal.ts                   # Tipos del terminal
    ├── utils/
    │   ├── ansiColors.ts                 # Códigos ANSI a CSS
    │   └── formatting.ts                 # Helpers de formato
    └── styles/
        └── terminal.css                  # Estilos del terminal
2.1 Terminal Component (components/Terminal/Terminal.tsx)
import { useEffect, useRef } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import 'xterm/css/xterm.css';
import { WebSocketEvent } from '../../types/events';

interface TerminalProps {
  events: WebSocketEvent[];
  onInput: (input: string) => void;
}

export function Terminal({ events, onInput }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const inputBufferRef = useRef<string>('');

  // Inicializar xterm.js
  useEffect(() => {
    if (!terminalRef.current) return;

    const xterm = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: '"JetBrains Mono", "Fira Code", Consolas, monospace',
      theme: {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        cursorAccent: '#0d1117',
        selection: '#1f6feb4d',
        black: '#484f58',
        red: '#ff7b72',
        green: '#3fb950',
        yellow: '#d29922',
        blue: '#58a6ff',
        magenta: '#bc8cff',
        cyan: '#39c5cf',
        white: '#b1bac4',
        brightBlack: '#6e7681',
        brightRed: '#ffa198',
        brightGreen: '#56d364',
        brightYellow: '#e3b341',
        brightBlue: '#79c0ff',
        brightMagenta: '#d2a8ff',
        brightCyan: '#56d4dd',
        brightWhite: '#f0f6fc',
      },
      rows: 30,
      cols: 120,
      scrollback: 10000,
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();
    
    xterm.loadAddon(fitAddon);
    xterm.loadAddon(webLinksAddon);
    xterm.open(terminalRef.current);
    fitAddon.fit();

    xtermRef.current = xterm;
    fitAddonRef.current = fitAddon;

    // Handle user input
    xterm.onData((data) => {
      switch (data) {
        case '\r': // Enter
          if (inputBufferRef.current.trim()) {
            onInput(inputBufferRef.current);
          }
          xterm.write('\r\n');
          inputBufferRef.current = '';
          break;
        
        case '\u007F': // Backspace
          if (inputBufferRef.current.length > 0) {
            inputBufferRef.current = inputBufferRef.current.slice(0, -1);
            xterm.write('\b \b');
          }
          break;
        
        case '\u0003': // Ctrl+C
          inputBufferRef.current = '';
          xterm.write('^C\r\n');
          break;
        
        default:
          // Printable characters
          if (data >= String.fromCharCode(0x20) && data <= String.fromCharCode(0x7E)) {
            inputBufferRef.current += data;
            xterm.write(data);
          }
      }
    });

    // Handle window resize
    const handleResize = () => fitAddon.fit();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      xterm.dispose();
    };
  }, [onInput]);

  // Renderizar eventos
  useEffect(() => {
    const xterm = xtermRef.current;
    if (!xterm || events.length === 0) return;

    const latestEvent = events[events.length - 1];
    renderEvent(xterm, latestEvent);
  }, [events]);

  return (
    <div 
      ref={terminalRef} 
      style={{ 
        width: '100%', 
        height: '100vh',
        padding: '8px'
      }} 
    />
  );
}

function renderEvent(xterm: XTerm, event: WebSocketEvent) {
  switch (event.type) {
    case 'connected':
      xterm.writeln('\x1b[35m╔══════════════════════════════════════════════════════════════╗\x1b[0m');
      xterm.writeln('\x1b[35m║                                                              ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██████╗  █████╗ ██╗   ██╗███████╗                          ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██╔══██╗██╔══██╗██║   ██║██╔════╝                          ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██║  ██║███████║██║   ██║█████╗                            ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██║  ██║██╔══██║╚██╗ ██╔╝██╔══╝                            ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██████╔╝██║  ██║ ╚████╔╝ ███████╗                          ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ╚═════╝ ╚═╝  ╚═╝  ╚═══╝  ╚══════╝                          ║\x1b[0m');
      xterm.writeln('\x1b[35m║                                                              ║\x1b[0m');
      xterm.writeln('\x1b[35m║    █████╗  ██████╗ ███████╗███╗   ██╗████████╗               ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝               ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║                  ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║                  ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║                  ║\x1b[0m');
      xterm.writeln('\x1b[35m║   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝                  ║\x1b[0m');
      xterm.writeln('\x1b[35m║                                                              ║\x1b[0m');
      xterm.writeln(`\x1b[35m║              Intelligent Development Agent                   ║\x1b[0m`);
      xterm.writeln(`\x1b[35m║                    Version ${event.version}                             ║\x1b[0m`);
      xterm.writeln('\x1b[35m╚══════════════════════════════════════════════════════════════╝\x1b[0m');
      xterm.writeln('');
      xterm.write('\x1b[36mYou:\x1b[0m ');
      break;

    case 'agent_message':
      xterm.writeln(`\n\x1b[32m${event.agent}:\x1b[0m ${event.content}`);
      xterm.write('\x1b[36mYou:\x1b[0m ');
      break;

    case 'thinking':
      xterm.writeln(`\x1b[90m💭 ${event.agent}: ${event.content}\x1b[0m`);
      break;

    case 'tool_call':
      xterm.writeln(`\x1b[33m🔧 ${event.agent} > ${event.tool_name}\x1b[0m`);
      break;

    case 'tool_result':
      const icon = event.success ? '✅' : '❌';
      xterm.writeln(`\x1b[90m${icon} ${event.tool_name}: ${event.result.substring(0, 100)}...\x1b[0m`);
      break;

    case 'error':
      xterm.writeln(`\x1b[31m✗ Error: ${event.message}\x1b[0m`);
      break;

    case 'success':
      xterm.writeln(`\x1b[32m✓ ${event.message}\x1b[0m`);
      break;

    case 'info':
      const prefix = event.prefix ? `${event.prefix}: ` : 'ℹ ';
      xterm.writeln(`\x1b[34m${prefix}${event.message}\x1b[0m`);
      break;
  }
}
2.2 WebSocket Hook (hooks/useWebSocket.ts)
import { useEffect, useState, useCallback, useRef } from 'react';
import { WebSocketEvent } from '../types/events';

interface UseWebSocketReturn {
  events: WebSocketEvent[];
  sendCommand: (content: string) => void;
  status: 'connecting' | 'connected' | 'disconnected';
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents(prev => [...prev, data]);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('disconnected');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setStatus('disconnected');
    };

    return () => {
      ws.close();
    };
  }, [url]);

  const sendCommand = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        command: 'execute',
        content
      }));
    }
  }, []);

  return { events, sendCommand, status };
}
2.3 App Component (App.tsx)
import { Terminal } from './components/Terminal/Terminal';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const { events, sendCommand, status } = useWebSocket('ws://localhost:8000/ws/agent');

  if (status === 'connecting') {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100vh',
        backgroundColor: '#0d1117',
        color: '#c9d1d9',
        fontFamily: 'monospace'
      }}>
        ⏳ Connecting to DaveAgent...
      </div>
    );
  }

  if (status === 'disconnected') {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100vh',
        backgroundColor: '#0d1117',
        color: '#ff7b72',
        fontFamily: 'monospace'
      }}>
        ❌ Disconnected. Refresh to reconnect.
      </div>
    );
  }

  return <Terminal events={events} onInput={sendCommand} />;
}

export default App;
FASE 3: Features Avanzadas (1-2 días)
✅ Syntax highlighting para código (react-syntax-highlighter)
✅ Diff viewer para cambios (react-diff-view)
✅ File autocomplete con @
✅ Historial de comandos (↑↓)
✅ Copy/paste support
✅ Exportar sesión a JSON
🚀 COMANDOS DE INSTALACIÓN
Backend:
cd DaveAgent
pip install fastapi uvicorn websockets
Frontend:
npm create vite@latest daveagent-web -- --template react-ts
cd daveagent-web
npm install xterm xterm-addon-fit xterm-addon-web-links
npm install react-syntax-highlighter react-diff-view
npm install -D @types/react-syntax-highlighter
✅ VENTAJAS DE ESTA ARQUITECTURA
✅ Separación total: Frontend maneja 100% de UI
✅ Backend stateless: Solo lógica de negocio
✅ Escalable: Puedes cambiar UI sin tocar backend
✅ Testeable: Backend y frontend se testean independientemente
✅ Reutilizable: El backend puede servir otros clientes (CLI, mobile, etc.)
🚀 ¿Empezamos con Fase 1?
¿Creo los archivos del backend?
✅ src/api/event_emitter.py
✅ src/api/server.py
✅ Modificar src/main.py para emitir eventos
✅ Actualizar pyproject.toml