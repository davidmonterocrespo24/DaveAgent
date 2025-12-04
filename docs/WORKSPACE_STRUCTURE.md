# Estructura del Workspace de DaveAgent

## Descripción

Todos los datos de DaveAgent se guardan **localmente en el workspace actual** (el directorio donde ejecutas `daveagent`), dentro de la carpeta `.daveagent/`.

Esto facilita:
- ✅ **Portabilidad**: Cada proyecto tiene su propia configuración y memoria
- ✅ **Organización**: Todo relacionado con el proyecto está junto
- ✅ **Control de versiones**: Puedes agregar `.daveagent/` a `.gitignore` fácilmente
- ✅ **Múltiples proyectos**: Cada workspace es independiente

## Estructura del Directorio `.daveagent/`

```
<tu-proyecto>/
├── .daveagent/               # Directorio raíz de datos de DaveAgent
│   ├── logs/                 # Logs de ejecución
│   │   ├── daveagent_20251204_143022.log
│   │   ├── daveagent_20251204_150311.log
│   │   └── ...
│   │
│   ├── state/                # Estados de sesiones (AutoGen)
│   │   ├── session_20251204_143022.json
│   │   ├── session_20251204_150311.json
│   │   └── ...
│   │
│   ├── memory/               # Memoria vectorial (ChromaDB)
│   │   ├── chroma.sqlite3
│   │   ├── conversations/    # Colección: conversaciones
│   │   ├── codebase/         # Colección: código indexado
│   │   ├── decisions/        # Colección: decisiones arquitectónicas
│   │   ├── preferences/      # Colección: preferencias del usuario
│   │   └── user_info/        # Colección: información del usuario
│   │
│   └── conversations.json    # Historial de interacciones LLM
│
├── src/                      # Tu código fuente
├── tests/                    # Tus tests
├── README.md
└── ...
```

## Componentes y Rutas

### 1. Logs (`.daveagent/logs/`)

**Propósito**: Logs detallados de todas las operaciones de DaveAgent

**Formato**: `daveagent_YYYYMMDD_HHMMSS.log`

**Contenido**:
- Llamadas a API (modelo, tokens, latencia)
- Selección de agentes
- Procesamiento de tareas
- Errores y excepciones con traceback completo
- Operaciones de archivos
- Decisiones de planificación

**Configuración**: Ver [src/utils/logger.py:52](../src/utils/logger.py#L52)

### 2. Estado de Sesiones (`.daveagent/state/`)

**Propósito**: Estados guardados de agentes y teams (usando `save_state()` de AutoGen)

**Formato**: `session_YYYYMMDD_HHMMSS.json`

**Contenido**:
- Estado completo de agentes (historial de mensajes, contexto)
- Estado de teams (configuración, termination conditions)
- Metadata de sesión (título, tags, descripción, timestamps)
- Estadísticas (número de mensajes, agentes involucrados)

**Formato JSON**:
```json
{
  "session_id": "20251204_143022",
  "saved_at": "2025-12-04T14:35:12.123456",
  "session_metadata": {
    "title": "Feature Development",
    "tags": ["backend", "api"],
    "description": "Implementing REST endpoints",
    "created_at": "2025-12-04T14:30:22.000000",
    "last_interaction": "2025-12-04T14:35:12.000000"
  },
  "agent_states": {
    "coder": {
      "state": {
        "type": "AssistantAgentState",
        "version": "1.0.0",
        "llm_context": {
          "messages": [...]
        }
      },
      "metadata": {},
      "saved_at": "2025-12-04T14:35:12.000000"
    }
  },
  "team_states": {},
  "metadata": {
    "auto_save_enabled": true,
    "auto_save_interval": 300
  }
}
```

**Configuración**: Ver [src/managers/state_manager.py:46](../src/managers/state_manager.py#L46)

**Documentación**: Ver [STATE_MANAGER_USAGE.md](STATE_MANAGER_USAGE.md)

### 3. Memoria Vectorial (`.daveagent/memory/`)

**Propósito**: Búsqueda semántica de conversaciones, código, decisiones y preferencias

**Motor**: ChromaDB con embeddings de Sentence Transformers

**Colecciones**:

- **`conversations/`**: Historial de conversaciones para recuperación contextual
- **`codebase/`**: Código indexado del proyecto para búsqueda semántica
- **`decisions/`**: Decisiones arquitectónicas y patrones aplicados
- **`preferences/`**: Preferencias del usuario (estilo de código, frameworks)
- **`user_info/`**: Información sobre el usuario (expertise, metas del proyecto)

**Configuración**: Ver [src/memory/base_memory.py:48](../src/memory/base_memory.py#L48)

**Documentación**: Ver [MEMORY_SYSTEM.md](MEMORY_SYSTEM.md) (si existe)

### 4. Historial de Conversaciones (`.daveagent/conversations.json`)

**Propósito**: Log estructurado de todas las interacciones con modelos LLM

**Formato**: Array JSON con conversaciones ordenadas (más reciente primero)

**Contenido**:
```json
[
  {
    "id": "20251204_143522_123456",
    "timestamp": "2025-12-04T14:35:22.123456",
    "date": "2025-12-04",
    "time": "14:35:22",
    "agent": "Coder",
    "model": "deepseek-chat",
    "provider": "DeepSeek",
    "user_request": "Add authentication to the API",
    "agent_response": "I'll implement JWT-based authentication...",
    "metadata": {
      "prompt_tokens": 1234,
      "completion_tokens": 567,
      "tools_used": ["write_file", "read_file"]
    }
  },
  ...
]
```

**Configuración**: Ver [src/utils/conversation_tracker.py:15](../src/utils/conversation_tracker.py#L15)

## Gestión del Directorio `.daveagent/`

### Control de Versiones (Git)

**Recomendado**: Agregar a `.gitignore`

```gitignore
# DaveAgent data (local workspace data, do not commit)
.daveagent/
```

**Razón**:
- Los logs pueden ser muy grandes
- Las sesiones contienen historial de conversaciones (puede tener información sensible)
- La base de datos de ChromaDB es binaria y cambia constantemente

**Excepción**: Si quieres versionar algunas sesiones específicas, puedes hacerlo selectivamente:

```bash
git add .daveagent/state/session_important_feature.json
git commit -m "Save session state for important feature implementation"
```

### Limpieza

**Logs antiguos**:
```bash
# Eliminar logs de más de 30 días
find .daveagent/logs -name "*.log" -mtime +30 -delete
```

**Sesiones antiguas**:
```python
# Desde el CLI de DaveAgent
/delete-session <session_id>
```

**Memoria completa**:
```bash
# Borrar todo (CUIDADO: irreversible)
rm -rf .daveagent/memory
```

### Backup

**Backup completo del workspace**:
```bash
tar -czf daveagent-backup-$(date +%Y%m%d).tar.gz .daveagent/
```

**Backup solo de sesiones**:
```bash
tar -czf sessions-backup-$(date +%Y%m%d).tar.gz .daveagent/state/
```

**Restaurar**:
```bash
tar -xzf daveagent-backup-20251204.tar.gz
```

## Migración de Datos

### Desde Versión Anterior (Home Directory)

Si tienes datos en `~/.daveagent/` de versiones anteriores:

```bash
# Copiar todo al workspace actual
cp -r ~/.daveagent/* ./.daveagent/

# O selectivamente:
cp -r ~/.daveagent/state ./.daveagent/
cp -r ~/.daveagent/memory ./.daveagent/
```

### Entre Proyectos

**Compartir memoria entre proyectos** (no recomendado, pero posible):

```bash
# En proyecto 2, crear symlink a memoria de proyecto 1
cd proyecto2
ln -s ../proyecto1/.daveagent/memory ./.daveagent/memory
```

**Copiar sesión específica**:
```bash
cp proyecto1/.daveagent/state/session_XYZ.json proyecto2/.daveagent/state/
```

## Tamaño y Rendimiento

**Tamaños típicos**:
- Logs: ~1-5 MB por sesión (depende de verbosidad)
- State: ~100-500 KB por sesión (depende de historial de mensajes)
- Memory (ChromaDB): ~10-100 MB (depende del tamaño del codebase indexado)
- conversations.json: ~1-10 MB (crece con el uso)

**Optimización**:
- Los logs se crean por sesión (no se acumulan en un solo archivo)
- ChromaDB usa compresión y embeddings eficientes
- Las sesiones son independientes (puedes eliminar las viejas sin afectar las nuevas)

## Solución de Problemas

### "Permission Denied" al escribir en `.daveagent/`

**Causa**: Permisos insuficientes en el directorio

**Solución**:
```bash
chmod -R u+w .daveagent/
```

### "Directory not found" al iniciar

**Causa**: DaveAgent no puede crear el directorio

**Solución**: Asegúrate de tener permisos de escritura en el workspace:
```bash
ls -la .
```

### "Database locked" en ChromaDB

**Causa**: Otra instancia de DaveAgent está usando la base de datos

**Solución**: Cierra otras instancias o elimina el lock:
```bash
rm .daveagent/memory/chroma.lock
```

## Referencias

- **StateManager**: [src/managers/state_manager.py](../src/managers/state_manager.py)
- **MemoryManager**: [src/memory/base_memory.py](../src/memory/base_memory.py)
- **Logger**: [src/utils/logger.py](../src/utils/logger.py)
- **ConversationTracker**: [src/utils/conversation_tracker.py](../src/utils/conversation_tracker.py)
