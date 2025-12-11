# Sistema de Gestión de Sesiones Mejorado

## Resumen de Implementación

Se ha implementado un sistema completo de gestión de sesiones con visualización Rich del historial de conversaciones, basado en los tests exitosos de AutoGen save_state/load_state.

---

## ✨ Nuevas Funcionalidades

### 1. **Metadata Descriptiva de Sesiones**

Cada sesión ahora incluye:
- **Título**: Nombre descriptivo de la sesión
- **Tags**: Etiquetas para categorización
- **Descripción**: Descripción detallada del propósito
- **Created_at**: Timestamp de creación
- **Last_interaction**: Timestamp de última modificación
- **Total_messages**: Contador de mensajes en la sesión

### 2. **Visualización Rich con HistoryViewer**

Nueva clase `HistoryViewer` en `src/utils/history_viewer.py` que proporciona:

#### Visualización de Lista de Sesiones
```python
history_viewer.display_sessions_list(sessions)
```
- Tabla Rich con columnas: #, Título, ID, Mensajes, Última interacción, Tags
- Ordenadas por última interacción (más reciente primero)
- Formato amigable de fechas

#### Visualización de Metadata
```python
history_viewer.display_session_metadata(metadata, session_id)
```
- Panel Rich con información de la sesión
- Título, descripción, tags, timestamps formateados

#### Visualización de Historial de Conversación
```python
history_viewer.display_conversation_history(messages, max_messages, show_thoughts)
```
- Paneles Rich para cada mensaje
- Diferenciación visual entre usuario (azul) y agente (verde)
- Detección automática de código con syntax highlighting
- Renderizado de Markdown
- Opción para mostrar razonamientos/thoughts

### 3. **Comandos Mejorados**

#### `/new-session <título> [--tags tag1,tag2] [--desc descripción]`
Crea una nueva sesión con metadata completa:
```bash
/new-session "Proyecto API REST" --tags backend,python,fastapi --desc "Desarrollo de API con autenticación"
```

#### `/save-session [título]`
Guarda la sesión actual:
- Si NO hay sesión activa → crea nueva con título opcional
- Si HAY sesión activa → actualiza la sesión existente
```bash
/save-session "Actualización importante"
```

#### `/load-session [session_id]`
Carga una sesión y muestra el historial completo:
- Sin argumentos → carga la sesión más reciente
- Con session_id → carga sesión específica
- Muestra automáticamente:
  - Metadata de la sesión
  - Últimos 20 mensajes del historial
  - Estadísticas de restauración
```bash
/load-session 20250105_143000
/load-session
```

#### `/sessions` o `/list-sessions`
Lista todas las sesiones con tabla Rich:
- Ordenadas por última interacción
- Muestra: título, ID, mensajes, fecha, tags

#### `/history [--all] [--thoughts] [session_id]`
Muestra el historial de conversación:
- Sin argumentos → últimos 20 mensajes de sesión actual
- `--all` → todos los mensajes sin límite
- `--thoughts` → incluye razonamientos del agente
- `session_id` → historial de sesión específica
```bash
/history
/history --all
/history --thoughts
/history 20250105_143000
```

### 4. **Auto-Resume al Iniciar**

Al iniciar la aplicación:
1. Detecta si existen sesiones previas
2. Muestra información de la sesión más reciente
3. Pregunta al usuario si desea continuar
4. Si acepta:
   - Carga el estado completo
   - Restaura todos los agentes
   - Muestra últimos 5 mensajes
   - Permite continuar desde donde quedó

```
📋 Sesión anterior encontrada:
  • Título: Proyecto API REST
  • Última interacción: 2025-01-05 14:30
  • Mensajes: 25

¿Deseas continuar con esta sesión? (S/n):
```

---

## 🔧 Cambios Técnicos

### StateManager (`src/managers/state_manager.py`)

#### Métodos Nuevos:
- `start_session(session_id, title, tags, description)` - Inicia sesión con metadata
- `get_session_history(session_id)` - Extrae historial de mensajes
- `get_session_metadata(session_id)` - Obtiene metadata de sesión

#### Métodos Mejorados:
- `list_sessions()` - Ahora incluye metadata completa y contador de mensajes
- `save_to_disk()` - Guarda session_metadata y actualiza last_interaction
- `load_from_disk()` - Carga session_metadata junto con estados

### HistoryViewer (`src/utils/history_viewer.py`)

Clase nueva con métodos:
- `display_sessions_list(sessions)` - Tabla de sesiones
- `display_session_metadata(metadata, session_id)` - Panel de metadata
- `display_conversation_history(messages, max_messages, show_thoughts)` - Historial formateado
- `display_session_loaded(session_id, total_messages, agents_restored)` - Confirmación de carga
- `display_no_sessions()` - Mensaje cuando no hay sesiones
- `display_loading_session(session_id, title)` - Indicador de carga

### main.py

#### Métodos Nuevos:
- `_new_session_command(parts)` - Comando /new-session
- `_show_history_command(parts)` - Comando /history
- `_check_and_resume_session()` - Auto-resume al inicio

#### Métodos Mejorados:
- `_save_state_command(parts)` - Ahora usa metadata de sesión
- `_load_state_command(parts)` - Muestra historial automáticamente
- `_list_sessions_command()` - Usa HistoryViewer con Rich
- `run()` - Llama a `_check_and_resume_session()` al inicio

---

## 📊 Flujo de Trabajo Típico

### Sesión Nueva
```bash
# 1. Crear sesión con nombre descriptivo
/new-session "Proyecto Web Backend" --tags python,api,backend

# 2. Trabajar normalmente
Usuario: "Create a FastAPI application with user authentication"
Agente: [realiza el trabajo...]

# 3. Guardar (se guarda automáticamente cada 5 min, pero puedes forzar)
/save-session

# 4. Salir
/exit
```

### Continuar Sesión
```bash
# 1. Iniciar aplicación - aparece prompt de auto-resume
¿Deseas continuar con esta sesión? (S/n): s

# 2. Ver todo el historial si necesitas contexto
/history --all

# 3. Continuar trabajando
Usuario: "Now add password hashing with bcrypt"
Agente: [continúa desde donde quedó...]

# 4. Guardar cambios
/save-session
```

### Gestionar Múltiples Sesiones
```bash
# 1. Ver todas las sesiones
/sessions

# 2. Cargar sesión específica
/load-session 20250105_143000

# 3. Ver historial de esa sesión
/history

# 4. O ver historial de otra sesión sin cargarla
/history 20250104_120000
```

---

## 🎯 Beneficios

1. **Contexto Completo**: El agente recuerda TODO entre sesiones
2. **Organización**: Sesiones con nombres y tags facilitan encontrar trabajos previos
3. **Visualización Clara**: Rich panels y tablas hacen el historial legible
4. **Continuidad**: Auto-resume permite retomar trabajo inmediatamente
5. **Flexibilidad**: Múltiples sesiones paralelas sin interferencia
6. **Persistencia Confiable**: AutoGen save_state garantiza que no se pierde nada

---

## 🔍 Estructura del Estado Guardado

```json
{
  "session_id": "20250105_143000",
  "saved_at": "2025-01-05T14:30:45.123456",
  "session_metadata": {
    "title": "Proyecto API REST",
    "tags": ["backend", "python", "fastapi"],
    "description": "Desarrollo de API con autenticación",
    "created_at": "2025-01-05T14:00:00.000000",
    "last_interaction": "2025-01-05T14:30:45.123456"
  },
  "agent_states": {
    "coder": {
      "state": {
        "type": "AssistantAgentState",
        "version": "1.0.0",
        "llm_context": {
          "messages": [
            {
              "content": "Usuario: mensaje...",
              "source": "user",
              "type": "UserMessage"
            },
            {
              "content": "Agente: respuesta...",
              "source": "coder",
              "type": "AssistantMessage"
            }
          ]
        }
      },
      "metadata": {
        "description": "Main coder agent with tools"
      },
      "saved_at": "2025-01-05T14:30:45.123456"
    }
    // ... otros agentes
  }
}
```

---

## ✅ Tests Validados

Los siguientes tests confirman que la funcionalidad está correcta:

1. ✅ `test_autogen_state_basics.py` - Save/load básico funciona
2. ✅ `test_autogen_state_sessions.py` - Múltiples sesiones funcionan
3. ✅ `test_autogen_state_history_viewer.py` - Visualización Rich funciona
4. ✅ `test_autogen_state_resume.py` - Resume completo funciona

Todos los tests pasaron exitosamente mostrando que el sistema de AutoGen save_state/load_state mantiene el contexto completo entre sesiones.

---

## 📝 Notas Importantes

1. **Auto-Save**: El estado se guarda automáticamente cada 5 minutos y al cerrar
2. **Ubicación**: Las sesiones se guardan en `~/.daveagent/state/session_*.json`
3. **Sin Compresión**: No se necesita compresión manual, AutoGen maneja el contexto
4. **Búsqueda Semántica**: Los mensajes también se guardan en memoria vectorial para búsqueda
5. **Metadata Editable**: Puedes agregar más campos a `session_metadata` según necesites

---

## 🚀 Próximos Pasos Posibles

- [ ] Búsqueda de sesiones por tags
- [ ] Exportar sesiones a formato Markdown/HTML
- [ ] Fusionar sesiones relacionadas
- [ ] Estadísticas de uso por sesión
- [ ] Backup automático de sesiones importantes
- [ ] Compartir sesiones entre usuarios (export/import)

---

**Implementado el:** 2025-01-05  
**Basado en:** Tests exitosos de AutoGen save_state/load_state  
**Versión:** 1.0.0
