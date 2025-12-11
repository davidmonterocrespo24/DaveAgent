# Migración a AutoGen save_state/load_state

## 📋 Resumen

Este documento explica la migración del sistema de gestión de historial desde archivos JSON personalizados hacia el sistema oficial de AutoGen `save_state()` y `load_state()`.

## 🎯 Objetivo

Usar el sistema oficial de AutoGen para persistir el estado completo de los agentes, incluyendo todo el contexto de conversación, entre sesiones.

## ✅ Cambios Realizados

### 1. **Comandos Eliminados** ❌

Se eliminaron los comandos legacy que guardaban el historial en archivos personalizados:

- `/save <archivo>` - ELIMINADO
- `/load <archivo>` - ELIMINADO

**Razón:** Duplicaban funcionalidad y no usaban el sistema oficial de AutoGen.

### 2. **ConversationManager Simplificado** 🔄

El `ConversationManager` ahora solo maneja el historial **en memoria** durante la sesión activa:

**ANTES:**
```python
class ConversationManager:
    def __init__(self, max_tokens: int = 8000, summary_threshold: int = 6000):
        self.conversation_history = []
        self.summary = None
        self.compressed_count = 0
    
    def save_to_file(self, filepath: str):
        # Guardar a JSON personalizado
    
    def load_from_file(self, filepath: str):
        # Cargar desde JSON personalizado
    
    def needs_compression(self) -> bool:
        # Lógica de compresión manual
    
    def compress_history(self, summary_text: str):
        # Comprimir historial manualmente
```

**AHORA:**
```python
class ConversationManager:
    def __init__(self):
        self.conversation_history = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        # Solo para tracking en memoria
    
    def get_recent_messages(self, limit: int = 10):
        # Obtener mensajes recientes
    
    def get_statistics(self):
        # Estadísticas de la sesión
```

**Razón:** AutoGen maneja automáticamente el contexto de los agentes. No necesitamos compresión manual ni guardado a archivo.

### 3. **StateManager como Sistema Principal** ⭐

El `StateManager` ahora es el único responsable de persistir estado:

```python
# Uso del StateManager con AutoGen
state_manager = StateManager()

# Guardar estado de agente
await state_manager.save_agent_state("coder", coder_agent)

# Guardar estado de team
await state_manager.save_team_state("main_team", team)

# Persistir a disco
await state_manager.save_to_disk(session_id="my_session")

# Cargar desde disco
await state_manager.load_from_disk(session_id="my_session")

# Cargar estado en agente
await state_manager.load_agent_state("coder", coder_agent)
```

### 4. **Auto-Save Automático** 💾

El sistema guarda el estado automáticamente después de cada interacción:

```python
async def _auto_save_agent_states(self):
    """Auto-guarda el estado de todos los agentes"""
    # Guardar estado de cada agente
    await self.state_manager.save_agent_state("coder", self.coder_agent)
    await self.state_manager.save_agent_state("code_searcher", self.code_searcher.searcher_agent)
    await self.state_manager.save_agent_state("planning", self.planning_agent)
    await self.state_manager.save_agent_state("summary", self.summary_agent)
    
    # Guardar a disco
    await self.state_manager.save_to_disk()
```

Este método se llama automáticamente después de cada respuesta del agente.

## 🚀 Uso del Nuevo Sistema

### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `/save-state [session]` | Guarda estado completo usando AutoGen |
| `/load-state [session]` | Carga estado desde sesión guardada |
| `/list-sessions` | Lista todas las sesiones disponibles |

### Ejemplos

**Guardar estado manualmente:**
```bash
/save-state my_important_work
# → Guarda en ~/.daveagent/state/session_my_important_work.json
```

**Cargar estado:**
```bash
/load-state my_important_work
# → Restaura todos los agentes con su contexto completo
```

**Ver sesiones guardadas:**
```bash
/list-sessions
# → Muestra todas las sesiones con fechas y metadata
```

## 📁 Estructura de Estado

El estado guardado tiene esta estructura:

```json
{
  "session_id": "20251105_143022",
  "saved_at": "2025-11-05T14:30:22",
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
      "saved_at": "2025-11-05T14:30:22"
    },
    "code_searcher": { ... },
    "planning": { ... },
    "summary": { ... }
  },
  "team_states": {}
}
```

## 🔍 Qué se Guarda Automáticamente

Con AutoGen `save_state()`, se persiste:

- ✅ **Todo el historial de mensajes de cada agente** (UserMessage, AssistantMessage, ToolCallMessage, etc.)
- ✅ **Contexto completo de la conversación**
- ✅ **Estado interno de cada agente**
- ✅ **Estado del team** (incluye todos sus agentes)
- ✅ **Orden de mensajes y flujo de conversación**

**No necesitas:**
- ❌ Compresión manual del historial
- ❌ Guardar archivos JSON personalizados
- ❌ Gestionar límites de tokens manualmente

## 🔄 Migración de Sesiones Antiguas

Si tienes archivos `.json` guardados con el sistema antiguo (`/save`), necesitas:

1. **No son compatibles** con el nuevo sistema
2. Recomendación: Hacer las conversaciones importantes de nuevo con el sistema nuevo

**No hay migración automática** porque el formato es completamente diferente (AutoGen vs JSON personalizado).

## 📚 Ventajas del Nuevo Sistema

| Aspecto | Sistema Antiguo | Sistema Nuevo (AutoGen) |
|---------|----------------|------------------------|
| **Compatibilidad** | Personalizado | Estándar AutoGen oficial |
| **Gestión de contexto** | Manual | Automática |
| **Límites de tokens** | Manual | AutoGen lo maneja |
| **Compresión** | Manual | AutoGen decide cuándo necesita |
| **Restauración** | Parcial | Completa (agentes + teams) |
| **Mantenimiento** | Alto | Bajo |

## 🎓 Recursos

- [AutoGen State Management Docs](https://microsoft.github.io/autogen/docs/tutorial/state-management)
- `src/managers/state_manager.py` - Implementación completa
- `main.py` - Ver `_auto_save_agent_states()` para auto-save

## ⚠️ Notas Importantes

1. **Auto-save está SIEMPRE activo** - No necesitas `/save-state` a menos que quieras un checkpoint manual
2. **ConversationManager solo es para estadísticas** - El historial real lo maneja AutoGen
3. **Sesiones se guardan en** `~/.daveagent/state/` por defecto
4. **Los agentes mantienen TODO su contexto** - No hay pérdida de información entre sesiones

## 🐛 Troubleshooting

**Problema:** "El agente no recuerda conversaciones pasadas"
- **Solución:** Verifica que `/load-state` se ejecutó correctamente

**Problema:** "No veo mi sesión en `/list-sessions`"
- **Solución:** El auto-save puede tardar unos segundos. Usa `/save-state` para forzar guardado inmediato

**Problema:** "Error al cargar estado"
- **Solución:** Verifica que el `session_id` exista y que el archivo JSON no esté corrupto

---

**Última actualización:** 2025-11-05
**Versión:** 2.0 (AutoGen State Management)
