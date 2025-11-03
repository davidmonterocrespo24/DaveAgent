# Sistema de Memoria con ChromaDB

## Descripción General

DaveAgent utiliza un sistema de memoria vectorial avanzado basado en **ChromaDB** y **sentence-transformers** para mantener contexto persistente a través de sesiones. Esto permite que los agentes "recuerden" conversaciones anteriores, patrones de código, decisiones arquitectónicas y preferencias del usuario.

## Arquitectura de Memoria

El sistema de memoria está organizado en **4 colecciones vectoriales**:

### 1. **Conversation Memory** (`conversations`)
- **Propósito**: Almacenar historial de conversaciones entre el usuario y los agentes
- **Contenido**: Pares de pregunta-respuesta con metadatos
- **Uso**: Permite que los agentes recuerden conversaciones previas y proporcionen respuestas consistentes
- **Metadatos**:
  - `agents_used`: Lista de agentes que participaron
  - `tools_called`: Herramientas utilizadas
  - `interaction_id`: ID único de la interacción
  - `model`: Modelo LLM utilizado
  - `provider`: Proveedor del LLM

### 2. **Codebase Memory** (`codebase`)
- **Propósito**: Indexar el código fuente del proyecto para búsquedas rápidas
- **Contenido**: Chunks de código con contexto y metadatos
- **Uso**: Permite búsquedas semánticas de código sin necesidad de herramientas de grep
- **Metadatos**:
  - `file_path`: Ruta relativa del archivo
  - `language`: Lenguaje de programación
  - `chunk_index`: Índice del chunk dentro del archivo
  - `functions`: Lista de funciones en el chunk
  - `classes`: Lista de clases en el chunk

### 3. **Decision Memory** (`decisions`)
- **Propósito**: Almacenar decisiones arquitectónicas y patrones de solución
- **Contenido**: Decisiones tomadas con contexto y razonamiento
- **Uso**: El PlanningAgent puede consultar decisiones previas para mantener consistencia
- **Metadatos**:
  - `decision_summary`: Resumen de la decisión
  - `category`: Categoría (architecture, design, implementation)
  - `impact`: Nivel de impacto (low, medium, high)

### 4. **User Preferences Memory** (`preferences`)
- **Propósito**: Guardar preferencias del usuario (estilo de código, frameworks, etc.)
- **Contenido**: Preferencias explícitas e implícitas del usuario
- **Uso**: Todos los agentes tienen acceso para personalizar sus respuestas
- **Metadatos**:
  - `category`: Categoría (code_style, framework, tool, workflow)
  - `priority`: Prioridad (low, normal, high)

## Integración con Agentes

### **CodeSearcher**
```python
# Tiene acceso a codebase_memory
memory=[self.memory_manager.codebase_memory]
```
- Puede encontrar código relevante mediante búsqueda semántica
- Los resultados de búsqueda enriquecen el contexto sin necesidad de herramientas

### **Coder**
```python
# Tiene acceso a múltiples memorias
memory=[
    self.memory_manager.conversation_memory,  # Conversaciones previas
    self.memory_manager.codebase_memory,      # Código base
    self.memory_manager.preferences_memory    # Preferencias
]
```
- Puede recordar cómo resolvió problemas similares antes
- Sigue preferencias de estilo de código del usuario
- Tiene contexto del código base sin necesidad de leerlo explícitamente

### **PlanningAgent**
```python
# Tiene acceso a decision_memory
memory=[self.memory_manager.decision_memory]
```
- Consulta decisiones arquitectónicas previas
- Mantiene consistencia en la planificación
- Evita revertir decisiones ya tomadas

## Cómo Funciona

### 1. **Indexación Automática de Conversaciones**
Cada interacción usuario-agente se guarda automáticamente en `conversation_memory`:

```python
await self.memory_manager.add_conversation(
    user_input="Crear una API REST con FastAPI",
    agent_response="He creado la API con FastAPI...",
    metadata={
        "agents_used": ["Planner", "Coder"],
        "tools_called": ["write_file", "edit_file"]
    }
)
```

### 2. **Indexación Manual de Código Base**
Usa el comando `/index` para indexar tu proyecto:

```bash
DaveAgent> /index
```

Esto:
- Escanea el directorio actual recursivamente
- Ignora patrones comunes (node_modules, .git, etc.)
- Divide archivos en chunks de ~1500 caracteres
- Extrae funciones y clases
- Almacena en `codebase_memory` con embeddings

### 3. **Consulta Automática en Runtime**
Cuando un agente recibe una tarea, **automáticamente** consulta sus memorias:

```python
# AutoGen maneja esto internamente
# 1. El agente recibe: "Fix the authentication bug"
# 2. La memoria se consulta con la query
# 3. Se recuperan los top-k chunks más relevantes (k=5)
# 4. Se agregan al contexto del agente como SystemMessage
# 5. El agente responde con contexto enriquecido
```

### 4. **Persistencia**
Toda la memoria se guarda en: `~/.daveagent/memory/`

La memoria persiste entre sesiones - no necesitas reindexar cada vez.

## Comandos CLI

### `/index`
Indexa el proyecto actual en memoria vectorial:

```bash
DaveAgent> /index
📚 Indexando proyecto en memoria vectorial...
✅ Indexación completada!
  • Archivos indexados: 45
  • Chunks creados: 234
  • Archivos omitidos: 12
```

### `/memory`
Muestra estadísticas de memoria:

```bash
DaveAgent> /memory
🧠 Estadísticas de Memoria Vectorial

📚 Sistema de memoria activo con 4 colecciones:
  • Conversations: Historial de conversaciones
  • Codebase: Código fuente indexado
  • Decisions: Decisiones arquitectónicas
  • Preferences: Preferencias del usuario

💾 Ubicación: /home/user/.daveagent/memory
📊 Tamaño total: 12.34 MB
```

### `/memory clear`
Limpia toda la memoria (requiere confirmación):

```bash
DaveAgent> /memory clear
⚠️  ¿Estás seguro de que quieres borrar TODA la memoria?
Esto eliminará:
  • Historial de conversaciones
  • Código base indexado
  • Decisiones arquitectónicas
  • Preferencias del usuario

⚠️  Para confirmar, ejecuta: /memory clear confirm
```

## Configuración

### Parámetros del MemoryManager

```python
MemoryManager(
    persistence_path=None,  # Defaults to ~/.daveagent/memory
    embedding_model="all-MiniLM-L6-v2",  # Sentence transformer model
    k=5,  # Top-k results to retrieve
    score_threshold=0.3  # Minimum similarity score
)
```

### Parámetros del DocumentIndexer

```python
DocumentIndexer(
    memory=memory,
    chunk_size=1500,  # Characters per chunk
    ignore_patterns=[  # Patterns to ignore
        "node_modules", ".git", "__pycache__",
        ".venv", "dist", "build"
    ]
)
```

## Modelo de Embeddings

Por defecto, se usa **`all-MiniLM-L6-v2`** de Sentence Transformers:
- Rápido y ligero (~80MB)
- Buen balance entre velocidad y calidad
- Funciona offline (se descarga en la primera ejecución)

### Modelos Alternativos

Puedes cambiar el modelo en `MemoryManager`:

```python
# Más preciso pero más lento
embedding_model="all-mpnet-base-v2"

# Multilingüe
embedding_model="paraphrase-multilingual-MiniLM-L12-v2"

# Específico para código
embedding_model="microsoft/codebert-base"
```

## Ejemplos de Uso

### Ejemplo 1: Recordar Decisiones
```bash
User: "Should I use SQLAlchemy or raw SQL for this project?"
Planner: [consulta decision_memory]
Planner: "Based on our previous decision (2024-01-15), we chose
          SQLAlchemy for consistency with other services."
```

### Ejemplo 2: Encontrar Código Similar
```bash
User: "Create an authentication endpoint"
CodeSearcher: [consulta codebase_memory]
CodeSearcher: "Found similar auth code in api/auth.py:45-78.
               I'll use that pattern for consistency."
```

### Ejemplo 3: Mantener Preferencias
```bash
User: "Always use type hints in Python"
[Se guarda en preferences_memory]

[Sesión posterior]
Coder: [consulta preferences_memory antes de generar código]
Coder: [Genera código con type hints automáticamente]
```

## Consideraciones de Rendimiento

### Tamaño de Memoria
- Cada chunk de código: ~2KB
- Embedding por chunk: ~1KB
- 1000 chunks ≈ 3MB de memoria

### Velocidad de Consulta
- Primera consulta: ~200-500ms (carga del modelo)
- Consultas subsecuentes: ~50-100ms
- Indexación: ~1-2 archivos/segundo

### Límites Recomendados
- **Proyectos pequeños** (<100 archivos): Indexar todo
- **Proyectos medianos** (100-500 archivos): Indexar selectivamente
- **Proyectos grandes** (>500 archivos): Usar `max_files` parameter

## Troubleshooting

### "No module named 'chromadb'"
```bash
pip install -r requirements.txt
```

### "Sentence transformer model download failed"
- Requiere conexión a internet la primera vez
- El modelo se descarga a `~/.cache/torch/sentence_transformers/`

### "Memory directory not writable"
- Verifica permisos en `~/.daveagent/memory/`
- Cambia `persistence_path` si es necesario

### "Out of memory error"
- Reduce `k` (número de resultados)
- Reduce `chunk_size`
- Usa un modelo de embeddings más pequeño

## Roadmap

Mejoras futuras planeadas:

- [ ] **Memoria de errores**: Recordar errores comunes y soluciones
- [ ] **Memoria de tests**: Patrones de testing exitosos
- [ ] **Memoria de refactorings**: Historial de refactorizaciones
- [ ] **Query híbrida**: Combinar búsqueda semántica + keyword search
- [ ] **Reranking**: Mejorar relevancia con cross-encoder
- [ ] **Incremental indexing**: Solo indexar archivos modificados
- [ ] **Memory statistics**: Conteo exacto de documentos por colección
- [ ] **Memory export/import**: Compartir memoria entre equipos

## Referencias

- [AutoGen AgentChat Memory](https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/memory.html)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
