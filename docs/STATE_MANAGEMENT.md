# Sistema de Gestión de Estado

## Descripción General

DaveAgent implementa el sistema oficial de **AutoGen 0.4** para gestión de estado (`save_state` / `load_state`), permitiendo guardar y restaurar el contexto completo de los agentes entre sesiones.

## ¿Por Qué Usar Estado en Lugar de Solo Historial?

### Sistema Anterior (ConversationManager)
```python
# ❌ Solo guarda texto plano
{
  "conversation_history": [
    {"role": "user", "content": "Create an API"},
    {"role": "assistant", "content": "I created the API..."}
  ]
}
```

**Limitaciones:**
- No preserva el contexto interno del LLM
- Pierde el estado de herramientas y memoria
- No recuerda decisiones intermedias
- Requiere re-procesar toda la conversación

### Sistema Actual (StateManager con AutoGen)
```python
# ✅ Guarda el estado completo del agente
{
  "agent_states": {
    "coder": {
      "type": "AssistantAgentState",
      "llm_messages": [
        {"type": "UserMessage", "content": "Create an API"},
        {"type": "AssistantMessage", "content": "I created the API..."},
        {"type": "ToolCallMessage", "tool": "write_file", ...}
      ]
    }
  }
}
```

**Ventajas:**
- ✅ Preserva el contexto completo del LLM (model_context)
- ✅ Mantiene el historial de herramientas utilizadas
- ✅ Recuerda decisiones y razonamiento intermedio
- ✅ Continúa exactamente donde se quedó

## Arquitectura

### Componentes

```
StateManager
├── save_agent_state()     # Guarda estado de un agente individual
├── load_agent_state()     # Carga estado en un agente
├── save_to_disk()         # Persiste en JSON
├── load_from_disk()       # Carga desde JSON
├── list_sessions()        # Lista sesiones disponibles
└── auto-save (optional)   # Auto-guardado periódico
```

### Ubicación de Datos

```
~/.daveagent/state/
├── session_20240115_143022.json   # Sesión de ejemplo
├── session_20240115_150130.json
└── session_latest.json
```

### Formato de Sesión

```json
{
  "session_id": "20240115_143022",
  "saved_at": "2024-01-15T14:30:45",
  "agent_states": {
    "coder": {
      "state": {
        "type": "AssistantAgentState",
        "version": "1.0.0",
        "llm_messages": [...]
      },
      "metadata": {
        "description": "Main coder agent with tools"
      },
      "saved_at": "2024-01-15T14:30:45"
    },
    "code_searcher": {...},
    "planning": {...},
    "summary": {...}
  },
  "metadata": {
    "auto_save_enabled": true,
    "auto_save_interval": 300
  }
}
```

## Comandos CLI

### `/save-state [session_id]`

Guarda el estado completo de todos los agentes.

**Uso:**
```bash
# Auto-generar nombre de sesión (timestamp)
Tu: /save-state
✅ Estado guardado correctamente!
  • Session ID: 20240115_143022
  • Ubicación: ~/.daveagent/state/session_20240115_143022.json
  • Agentes guardados: 4

# Especificar nombre de sesión
Tu: /save-state my_api_project
✅ Estado guardado correctamente!
  • Session ID: my_api_project
  • Ubicación: ~/.daveagent/state/session_my_api_project.json
  • Agentes guardados: 4
```

**Qué se guarda:**
- Estado completo del `Coder` (incluye model_context con herramientas)
- Estado del `CodeSearcher` (incluye búsquedas previas)
- Estado del `PlanningAgent` (incluye planes y progreso)
- Estado del `SummaryAgent`

### `/load-state [session_id]`

Carga el estado de agentes desde una sesión guardada.

**Uso:**
```bash
# Cargar sesión más reciente
Tu: /load-state
Cargando sesión más reciente: 20240115_143022
✅ Estado cargado correctamente!
  • Session ID: 20240115_143022
  • Agentes restaurados: 4

# Cargar sesión específica
Tu: /load-state my_api_project
✅ Estado cargado correctamente!
  • Session ID: my_api_project
  • Agentes restaurados: 4
```

**Efecto:**
- Los agentes recuerdan EXACTAMENTE donde se quedaron
- Pueden continuar la conversación sin repetir contexto
- Mantienen conocimiento de herramientas ya utilizadas

### `/list-sessions`

Lista todas las sesiones guardadas.

**Uso:**
```bash
Tu: /list-sessions

📋 Sesiones Guardadas (3 total)

1. 20240115_150130
   Guardado: 2024-01-15T15:01:30
   Agentes: 4

2. my_api_project
   Guardado: 2024-01-15T14:30:45
   Agentes: 4

3. 20240115_143022
   Guardado: 2024-01-15T14:30:22
   Agentes: 4

💡 Usa /load-state <session_id> para cargar una sesión
```

## Auto-Save

El StateManager incluye auto-save opcional que guarda el estado automáticamente cada cierto intervalo.

### Configuración

```python
# En main.py
self.state_manager = StateManager(
    auto_save_enabled=True,      # Activar auto-save
    auto_save_interval=300       # Cada 5 minutos (300 segundos)
)
```

### Comportamiento

- **Guarda automáticamente** cada 5 minutos (configurable)
- **Solo guarda si hay cambios** (no crea archivos vacíos)
- **Corre en background** sin bloquear el agente
- **Guarda al cerrar** automáticamente en el finally block

## Integración con Memoria Vectorial

El StateManager y MemoryManager trabajan juntos:

| Sistema | Propósito | Persistencia |
|---------|-----------|--------------|
| **StateManager** | Contexto de conversación LLM | JSON (state/) |
| **MemoryManager** | Búsqueda semántica | ChromaDB (memory/) |

### Diferencias Clave

**StateManager (Estado):**
- Guarda el `model_context` completo del agente
- Permite continuar conversación EXACTAMENTE donde se quedó
- Incluye historial de herramientas y mensajes del sistema

**MemoryManager (Memoria):**
- Guarda conversaciones como embeddings vectoriales
- Permite búsqueda semántica de conversaciones pasadas
- No reemplaza el contexto, lo enriquece con información relevante

### Uso Combinado

```python
# Escenario: Retomar proyecto después de una semana

# 1. Cargar estado (contexto exacto de la última sesión)
Tu: /load-state my_api_project
✅ Estado cargado - El agente recuerda la conversación completa

# 2. Consultar memoria vectorial (buscar conversaciones relacionadas)
Tu: "Add authentication to the API"
# MemoryManager automáticamente:
# - Busca conversaciones previas sobre "authentication"
# - Añade contexto relevante al agente
# - El agente responde con conocimiento de patrones previos
```

## Ejemplos de Uso

### Ejemplo 1: Proyecto Multi-Sesión

```bash
# Día 1 - Iniciar proyecto
Tu: "Create a REST API with FastAPI for user management"
[Agente crea múltiples archivos, modelos, endpoints...]

Tu: /save-state user_api_v1
✅ Estado guardado

# Día 2 - Continuar proyecto
Tu: /load-state user_api_v1
✅ Estado cargado

Tu: "Add JWT authentication to the API"
# El agente RECUERDA:
# - Qué archivos creó
# - La estructura del proyecto
# - Las decisiones de diseño previas
# Puede continuar sin necesidad de re-explorar
```

### Ejemplo 2: Múltiples Proyectos

```bash
# Proyecto A
Tu: "Work on project A - create database models"
[Trabajo en proyecto A...]
Tu: /save-state project_a

# Proyecto B
Tu: "Work on project B - create API endpoints"
[Trabajo en proyecto B...]
Tu: /save-state project_b

# Volver a Proyecto A
Tu: /load-state project_a
# Contexto de proyecto A restaurado
# Proyecto B no interfiere
```

### Ejemplo 3: Debugging con Estados

```bash
# Antes de cambio arriesgado
Tu: /save-state before_refactor

Tu: "Refactor the authentication system"
[Algo sale mal...]

# Volver al estado anterior
Tu: /load-state before_refactor
# Estado restaurado antes del refactor
```

## API Programática

Si necesitas usar el StateManager programáticamente:

```python
from src.managers import StateManager

# Inicializar
state_manager = StateManager(
    auto_save_enabled=True,
    auto_save_interval=300
)

# Iniciar sesión
session_id = state_manager.start_session("my_session")

# Guardar estado de agente
await state_manager.save_agent_state(
    "coder",
    coder_agent,
    metadata={"project": "API", "phase": "development"}
)

# Guardar a disco
path = await state_manager.save_to_disk(session_id)
print(f"Estado guardado en: {path}")

# Cargar desde disco
loaded = await state_manager.load_from_disk("my_session")

# Restaurar en agente
await state_manager.load_agent_state("coder", coder_agent)

# Listar sesiones
sessions = state_manager.list_sessions()
for session in sessions:
    print(f"{session['session_id']}: {session['saved_at']}")

# Cerrar (auto-save final)
await state_manager.close()
```

## Comparación con Sistema Anterior

| Característica | ConversationManager (Antiguo) | StateManager (Nuevo) |
|----------------|-------------------------------|----------------------|
| **Formato** | JSON plano | AutoGen state format |
| **Contenido** | Solo texto de mensajes | Contexto completo del LLM |
| **Herramientas** | No preserva | Historial completo |
| **Continuación** | Requiere re-procesar | Continúa exactamente |
| **Compatibilidad** | Custom | Estándar AutoGen |
| **Auto-save** | Manual | Automático (opcional) |
| **Búsqueda** | Lineal | N/A (usar MemoryManager) |

## Mejores Prácticas

### 1. Guardar Estado Regularmente

```bash
# Al terminar una fase de trabajo
Tu: /save-state after_database_setup

# Antes de cambios significativos
Tu: /save-state before_refactor

# Al final del día
Tu: /save-state end_of_day_20240115
```

### 2. Nombres Descriptivos

```bash
# ✅ Bueno
Tu: /save-state api_v1_complete
Tu: /save-state auth_working
Tu: /save-state before_migration

# ❌ Evitar
Tu: /save-state test
Tu: /save-state abc
Tu: /save-state 123
```

### 3. Combinar con Memoria

```bash
# Indexar proyecto primero
Tu: /index

# Guardar estado después de trabajo
Tu: /save-state

# Cargar estado + memoria vectorial trabajan juntos
Tu: /load-state my_project
Tu: "Continue working on authentication"
# - StateManager restaura contexto exacto
# - MemoryManager añade patrones relevantes del código indexado
```

### 4. Limpieza Periódica

```bash
# Listar sesiones viejas
Tu: /list-sessions

# Eliminar manualmente (por ahora)
$ rm ~/.daveagent/state/session_old_project.json
```

## Troubleshooting

### "No state found for agent"

**Causa:** El agente no tiene estado guardado en la sesión cargada.

**Solución:**
```bash
# Verificar que la sesión existe
Tu: /list-sessions

# Intentar cargar sesión diferente
Tu: /load-state otra_sesion
```

### "Session not found"

**Causa:** El session_id no existe en disco.

**Solución:**
```bash
# Listar sesiones disponibles
Tu: /list-sessions

# Usar un session_id existente
Tu: /load-state 20240115_143022
```

### "Failed to load state"

**Causa:** Archivo de estado corrupto o incompatible.

**Solución:**
```bash
# Eliminar archivo corrupto
$ rm ~/.daveagent/state/session_problematic.json

# Crear nuevo estado
Tu: /save-state new_session
```

## Roadmap

Mejoras futuras planeadas:

- [ ] **Gestión de sesiones**: Comando `/delete-session` para borrar sesiones
- [ ] **Búsqueda de sesiones**: Buscar por contenido o metadata
- [ ] **Export/Import**: Compartir sesiones entre máquinas
- [ ] **Compresión**: Comprimir estados antiguos
- [ ] **Diff de estados**: Ver qué cambió entre sesiones
- [ ] **Snapshots automáticos**: Crear snapshots en puntos clave
- [ ] **Cloud sync**: Sincronizar estados con la nube (opcional)

## Referencias

- [AutoGen State Management Docs](https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/state.html)
- [AssistantAgent.save_state()](https://microsoft.github.io/autogen/dev/reference/python/autogen_agentchat/agents/assistant_agent.html#autogen_agentchat.agents.AssistantAgent.save_state)
- [RoundRobinGroupChat.save_state()](https://microsoft.github.io/autogen/dev/reference/python/autogen_agentchat/teams/round_robin_group_chat.html#autogen_agentchat.teams.RoundRobinGroupChat.save_state)
