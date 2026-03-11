# DaveAgent Web API

**Backend API sin UI** - Solo emite eventos JSON estructurados para el frontend React.

## 📋 Arquitectura

```
Frontend (React + TypeScript)
        ↑
        │ WebSocket (JSON Events)
        ↓
Backend (Python + FastAPI)
        ↓
DaveAgent Core (Agentes + Herramientas)
```

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
# Desde el directorio raíz del proyecto
pip install -e .

# O instalar solo las dependencias de servidor
pip install fastapi uvicorn[standard] websockets
```

### 2. Iniciar Servidor

```bash
# Modo normal
daveagent --server

# Con puerto personalizado
daveagent --server --port 8080

# Con debug habilitado (auto-reload)
daveagent --server --debug

# Con host específico
daveagent --server --host 127.0.0.1 --port 8000
```

### 3. Verificar Estado

```bash
# Health check
curl http://localhost:8000/api/health

# Listar sesiones
curl http://localhost:8000/api/sessions

# Listar archivos
curl http://localhost:8000/api/files?path=.
```

## 📡 WebSocket Protocol

### Conexión

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agent');
```

### Mensajes: Cliente → Servidor

```typescript
// Ejecutar comando o mensaje
{
  "command": "execute",
  "content": "create a new API endpoint"
}

// Listar sesiones
{
  "command": "list_sessions"
}

// Cargar sesión
{
  "command": "load_session",
  "content": "20250122_143000"
}
```

### Eventos: Servidor → Cliente

#### Conexión Establecida
```json
{
  "type": "connected",
  "version": "1.2.1",
  "session_id": null,
  "timestamp": "2025-01-22T14:30:00.000Z"
}
```

#### Mensaje de Agente
```json
{
  "type": "agent_message",
  "agent": "Coder",
  "content": "I'll create a new API endpoint...",
  "timestamp": "2025-01-22T14:30:01.000Z"
}
```

#### Pensamiento/Razonamiento
```json
{
  "type": "thinking",
  "agent": "Planner",
  "content": "Analyzing the request...",
  "timestamp": "2025-01-22T14:30:02.000Z"
}
```

#### Llamada a Herramienta
```json
{
  "type": "tool_call",
  "agent": "Coder",
  "tool_name": "write_file",
  "tool_args": {
    "target_file": "api/endpoints.py",
    "file_content": "..."
  },
  "timestamp": "2025-01-22T14:30:03.000Z"
}
```

#### Resultado de Herramienta
```json
{
  "type": "tool_result",
  "agent": "Coder",
  "tool_name": "write_file",
  "result": "File written successfully",
  "success": true,
  "timestamp": "2025-01-22T14:30:04.000Z"
}
```

#### Código con Syntax Highlighting
```json
{
  "type": "code",
  "code": "def hello():\n    print('Hello')",
  "filename": "example.py",
  "language": "python",
  "timestamp": "2025-01-22T14:30:05.000Z"
}
```

#### Diff de Cambios
```json
{
  "type": "diff",
  "diff": "--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,3 @@\n-old line\n+new line",
  "filename": "file.py",
  "timestamp": "2025-01-22T14:30:06.000Z"
}
```

#### Error
```json
{
  "type": "error",
  "message": "File not found",
  "context": "read_file",
  "timestamp": "2025-01-22T14:30:07.000Z"
}
```

#### Éxito
```json
{
  "type": "success",
  "message": "Task completed successfully",
  "timestamp": "2025-01-22T14:30:08.000Z"
}
```

#### Información
```json
{
  "type": "info",
  "message": "Processing your request...",
  "prefix": "System",
  "timestamp": "2025-01-22T14:30:09.000Z"
}
```

#### Ayuda
```json
{
  "type": "help",
  "sections": [
    {
      "title": "CONVERSATION",
      "icon": "💬",
      "commands": [
        {"cmd": "/help", "desc": "Show this help"}
      ]
    }
  ],
  "timestamp": "2025-01-22T14:30:10.000Z"
}
```

## 🔌 REST Endpoints

### GET /api/health
Health check del servidor

**Response:**
```json
{
  "status": "ok",
  "version": "1.2.1",
  "timestamp": "2025-01-22T14:30:00.000Z"
}
```

### GET /api/sessions
Lista todas las sesiones guardadas

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "20250122_143000",
      "title": "API Development",
      "created_at": "2025-01-22T14:30:00",
      "last_interaction": "2025-01-22T15:45:00",
      "total_messages": 25
    }
  ],
  "total": 1
}
```

### GET /api/files?path=<path>
Lista archivos y directorios

**Parameters:**
- `path` (optional): Ruta relativa al proyecto (default: ".")

**Response:**
```json
{
  "files": [
    {
      "name": "src",
      "path": "src",
      "is_dir": true,
      "size": 0
    },
    {
      "name": "main.py",
      "path": "src/main.py",
      "is_dir": false,
      "size": 15234
    }
  ],
  "path": ".",
  "total": 2
}
```

## 🧪 Testing

### Test con cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Listar archivos
curl http://localhost:8000/api/files
curl "http://localhost:8000/api/files?path=src"

# Listar sesiones
curl http://localhost:8000/api/sessions
```

### Test con Python

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/agent"

    async with websockets.connect(uri) as websocket:
        # Recibir evento de conexión
        response = await websocket.recv()
        print("Connected:", json.loads(response))

        # Enviar mensaje
        await websocket.send(json.dumps({
            "command": "execute",
            "content": "Hello, DaveAgent!"
        }))

        # Recibir respuestas
        while True:
            response = await websocket.recv()
            event = json.loads(response)
            print(f"[{event['type']}]", event)

asyncio.run(test_websocket())
```

### Test con websocat

```bash
# Instalar websocat
cargo install websocat

# Conectar al WebSocket
websocat ws://localhost:8000/ws/agent

# Enviar mensaje (pegar y presionar Enter)
{"command": "execute", "content": "/help"}
```

## 🏗️ Estructura de Archivos

```
src/api/
├── __init__.py              # Module exports
├── server.py                # FastAPI app + WebSocket handler
├── event_emitter.py         # EventEmitter class (reemplaza CLIInterface)
└── README.md                # Esta documentación
```

## 🔧 Desarrollo

### Modo Debug (Auto-reload)

```bash
daveagent --server --debug
```

Cuando cambies archivos Python, el servidor se recargará automáticamente.

### Logs

Los logs del servidor se muestran en la consola. Nivel de logging:
- Normal: `INFO`
- Debug: `DEBUG`

### CORS

El servidor permite requests desde:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React dev server)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

## 📚 Próximos Pasos

1. **Frontend React**: Ver `/daveagent-web/` para el frontend
2. **Deployment**: Configurar nginx/gunicorn para producción
3. **SSL**: Agregar certificados SSL para HTTPS/WSS
4. **Auth**: Implementar autenticación (JWT tokens)

## 🐛 Troubleshooting

### Error: "Missing dependencies for server mode"

```bash
pip install fastapi uvicorn websockets
```

### Error: "Port already in use"

```bash
# Usar otro puerto
daveagent --server --port 8001

# O matar el proceso usando el puerto
lsof -ti:8000 | xargs kill -9
```

### WebSocket se desconecta inmediatamente

- Verificar que el frontend envía mensajes JSON válidos
- Verificar CORS en el navegador
- Revisar logs del servidor (`--debug`)

## 📖 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [uvicorn Documentation](https://www.uvicorn.org/)
