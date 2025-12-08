# 🏗️ Arquitectura de CodeAgent

Esta página describe la arquitectura técnica de CodeAgent, sus componentes principales y cómo interactúan entre sí.

## 📊 Visión General

CodeAgent sigue una arquitectura modular basada en agentes especializados, donde cada componente tiene responsabilidades claramente definidas.

```
┌─────────────────────────────────────────────────────────┐
│                    Usuario (CLI)                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              CLI Interface (Rich)                        │
│           prompt-toolkit + Rich formatting               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           Conversation Manager                           │
│  - Gestión de historial                                 │
│  - Compresión automática                                │
│  - Estimación de tokens                                 │
└────────────────────┬────────────────────────────────────┘
                     │
       ┌─────────────┴──────────────┐
       │                            │
┌──────▼───────┐          ┌────────▼────────┐
│ Complexity   │          │   Memory        │
│  Detector    │          │   System        │
└──────┬───────┘          │  (ChromaDB)     │
       │                  └─────────────────┘
       │
┌──────▼────────────────────────────────────────────────┐
│            Agent Router                                │
│  Determina: SIMPLE vs COMPLEX workflow                │
└──────┬────────────────────────────────────────────────┘
       │
       ├─── SIMPLE ───┐
       │              │
       │      ┌───────▼──────────────────┐
       │      │   Direct Execution        │
       │      │   - Coder Agent           │
       │      │   - Code Searcher         │
       │      └──────────────────────────┘
       │
       └─── COMPLEX ──┐
                      │
              ┌───────▼──────────────────┐
              │  Planning Workflow        │
              │  ┌─────────────────────┐ │
              │  │ Planning Agent      │ │
              │  └──────┬──────────────┘ │
              │         │                 │
              │  ┌──────▼──────────────┐ │
              │  │ SelectorGroupChat   │ │
              │  │  - CodeSearcher     │ │
              │  │  - Coder            │ │
              │  │  - Summary          │ │
              │  └─────────────────────┘ │
              └──────────────────────────┘
                      │
              ┌───────▼──────────────────┐
              │     Tools (45+)          │
              │  - Filesystem (7)        │
              │  - Git (8)               │
              │  - Data (15)             │
              │  - Web (7)               │
              │  - Analysis (5)          │
              │  - Memory (8)            │
              └──────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
CodeAgent/
├── src/                          # Código fuente principal
│   ├── __init__.py
│   │
│   ├── agents/                   # 🤖 Agentes del sistema
│   │   ├── __init__.py
│   │   ├── task_planner.py       # Planificador de tareas
│   │   ├── task_executor.py      # Ejecutor de tareas
│   │   └── code_searcher.py      # Búsqueda de código
│   │
│   ├── managers/                 # 📊 Gestores del sistema
│   │   ├── __init__.py
│   │   └── conversation_manager.py  # Gestión de conversación
│   │
│   ├── interfaces/               # 🖥️ Interfaces de usuario
│   │   ├── __init__.py
│   │   └── cli_interface.py      # Interfaz CLI con Rich
│   │
│   ├── config/                   # ⚙️ Configuración
│   │   ├── __init__.py
│   │   └── prompts.py            # Prompts del sistema
│   │
│   ├── memory/                   # 🧠 Sistema de memoria
│   │   ├── __init__.py
│   │   ├── memory_manager.py     # Gestor de memoria RAG
│   │   ├── chroma_manager.py     # Interfaz ChromaDB
│   │   └── embeddings.py         # Generación de embeddings
│   │
│   ├── observability/            # 📈 Observabilidad
│   │   ├── __init__.py
│   │   └── langfuse_tracer.py    # Trazado Langfuse
│   │
│   ├── utils/                    # 🔧 Utilidades
│   │   ├── __init__.py
│   │   ├── logger.py             # Sistema de logging
│   │   ├── file_utils.py         # Utilidades de archivos
│   │   └── token_counter.py      # Conteo de tokens
│   │
│   ├── tools/                    # 🛠️ Herramientas (45+)
│   │   ├── __init__.py           # Exporta todas las herramientas
│   │   │
│   │   ├── filesystem/           # 📁 Operaciones de archivos (7)
│   │   │   ├── __init__.py
│   │   │   └── file_operations.py
│   │   │
│   │   ├── git/                  # 🔀 Operaciones Git (8)
│   │   │   ├── __init__.py
│   │   │   └── git_operations.py
│   │   │
│   │   ├── data/                 # 📊 Datos (15)
│   │   │   ├── __init__.py
│   │   │   ├── json_tools.py     # JSON (8 herramientas)
│   │   │   └── csv_tools.py      # CSV (7 herramientas)
│   │   │
│   │   ├── web/                  # 🌐 Web (7)
│   │   │   ├── __init__.py
│   │   │   └── wikipedia_tools.py
│   │   │
│   │   └── analysis/             # 🔍 Análisis (5)
│   │       ├── __init__.py
│   │       ├── code_analyzer.py  # Análisis Python
│   │       └── search_tools.py   # Búsqueda y grep
│   │
│   ├── cli.py                    # Punto de entrada CLI
│   └── main.py                   # Aplicación principal
│
├── eval/                         # 🧪 Evaluación SWE-bench
│   ├── agent_wrapper.py          # Wrapper del agente
│   ├── run_inference.py          # Ejecución de inferencia
│   └── README.md                 # Documentación de evaluación
│
├── docs/                         # 📖 Documentación
│   ├── STRUCTURE.md              # Estructura del proyecto
│   ├── MEMORY_SYSTEM.md          # Sistema de memoria
│   ├── CODESEARCHER_GUIDE.md     # Guía de CodeSearcher
│   └── ...                       # Otros documentos
│
├── test/                         # ✅ Tests
│   ├── test_tools.py
│   ├── test_agents.py
│   └── ...
│
├── .daveagent/                   # Configuración local
│   ├── .env                      # Variables de entorno
│   └── memory/                   # Base de datos ChromaDB
│
├── logs/                         # 📄 Logs de ejecución
│
├── requirements.txt              # Dependencias
├── pyproject.toml                # Configuración del proyecto
├── setup.py                      # Script de instalación
└── README.md                     # Documentación principal
```

---

## 🧩 Componentes Principales

### 1. **CLI Interface** (`src/interfaces/cli_interface.py`)

**Responsabilidades**:
- Interfaz de usuario interactiva usando `prompt-toolkit`
- Formateo rico con `rich` (colores, tablas, paneles)
- Autocompletado de comandos y archivos
- Manejo de comandos especiales (`/help`, `/search`, etc.)

**Tecnologías**:
- `prompt-toolkit`: Autocompletado y navegación
- `rich`: Formateo de salida y colores

### 2. **Conversation Manager** (`src/managers/conversation_manager.py`)

**Responsabilidades**:
- Gestión del historial de conversación
- Estimación de uso de tokens
- Compresión automática cuando el historial crece
- Mantiene contexto relevante para los agentes

**Características**:
```python
- max_tokens: 8000 (límite máximo)
- summary_threshold: 6000 (umbral para comprimir)
- Algoritmo: Mantiene últimos 3 mensajes + resumen
```

### 3. **Complexity Detector**

**Responsabilidades**:
- Analiza la solicitud del usuario
- Determina si requiere flujo SIMPLE o COMPLEX
- Usa LLM para clasificación inteligente

**Criterios**:
```python
SIMPLE:
  - 1-5 archivos
  - Modificaciones directas
  - Búsquedas de código
  - Operaciones Git

COMPLEX:
  - 6+ archivos
  - Sistemas completos
  - Requiere pl anificación
  - Arquitectura multi-componente
```

### 4. **Agentes Especializados** (`src/agents/`)

#### A) **PlanningAgent** (Solo para COMPLEX)
- Crea planes de ejecución estructurados
- Rastrea progreso de tareas
- Re-planifica dinámicamente si es necesario
- NO tiene herramientas, solo planifica

#### B) **CodeSearcher** (Ambos workflows)
- Búsqueda y análisis de código
- NO modifica código
- Usa: `grep_search`, `read_file`, `analyze_python_file`
- Proporciona ubicaciones y referencias

#### C) **Coder** (Ambos workflows)
- Ejecuta modificaciones de código
- Tiene acceso a TODAS las 45+ herramientas
- Crea, edita y elimina archivos
- Ejecuta comandos Git

#### D) **SummaryAgent** (Ambos workflows)
- Crea resúmenes finales
- Lista archivos creados/modificados
- Identifica próximos pasos
- Marca tarea como completada

###  5. **Sistema de Memoria** (`src/memory/`)

**Arquitectura**:
```
Memory Manager
    │
    ├── ChromaDB (Base de datos vectorial)
    │   ├── conversations (historial)
    │   ├── codebase (código indexado)
    │   ├── decisions (decisiones arquitéctonicas)
    │   ├── preferences (preferencias del usuario)
    │   └── user_info (información del usuario)
    │
    └── Embeddings (BGE M3-Embedding)
        - Generación de vectores
        - Búsqueda semántica
```

**Herramientas de Memoria** (8):
- `query_conversation_memory`: Buscar conversaciones pasadas
- `query_codebase_memory`: Buscar en código indexado
- `query_decision_memory`: Recordar decisiones
- `query_preferences_memory`: Preferencias del usuario
- `query_user_memory`: Información del usuario
- `save_user_info`: Guardar info del usuario
- `save_decision`: Registrar decisión
- `save_preference`: Guardar preferencia

### 6. **Sistema de Herramientas** (`src/tools/`)

**Organización por Categoría**:

| Categoría | Cantidad | Ubicación | Descripción |
|-----------|----------|-----------|-------------|
| **Filesystem** | 7 | `tools/filesystem/` | Operaciones de archivos |
| **Git** | 8 | `tools/git/` | Control de versiones |
| **JSON** | 8 | `tools/data/json_tools.py` | Procesamiento JSON |
| **CSV** | 7 | `tools/data/csv_tools.py` | Análisis CSV |
| **Web** | 7 | `tools/web/` | Wikipedia, búsqueda web |
| **Analysis** | 5 | `tools/analysis/` | Análisis de código |
| **Memory** | 8 | Integradas en Memory Manager | RAG y persistencia |

### 7. **Observabilidad** (`src/observability/`)

**Langfuse Integration**:
- Trazado de llamadas LLM
- Métricas de rendimiento
- Análisis de costos
- Debugging de agentes

---

## 🔄 Flujos de Trabajo

### Flujo SIMPLE (Tareas Directas)

```
Usuario → CLI Interface → Conversation Manager
    ↓
Complexity Detector (→ SIMPLE)
    ↓
Selector: CodeSearcher o Coder
    ↓
┌─ CodeSearcher (si necesita búsqueda)
│   └─ Análisis y referencias
└─ Coder (ejecución directa)
    └─ Herramientas (read_file, write_file, git, etc.)
    ↓
Summary Agent
    └─ Resumen final
```

**Ejemplo**:
```
Usuario: "Fix the bug in auth.py line 45"
  → Coder lee auth.py
  → Coder aplica edit_file
  → Summary muestra cambios
```

### Flujo COMPLEX (Proyectos Multi-paso)

```
Usuario → CLI Interface → Conversation Manager
    ↓
Complexity Detector (→ COMPLEX)
    ↓
Planning Agent
    ↓
Crea Plan:
  1. [ ] Buscar estructura existente
  2. [ ] Crear modelos
  3. [ ] Implementar endpoints
  4. [ ] Agregar tests
    ↓
SelectorGroupChat
    ├─ Tarea 1 → CodeSearcher (busca estructura)
    │           └─ Planning Agent actualiza plan
    ├─ Tarea 2 → Coder (crea modelos)
    │           └─ Planning Agent actualiza plan
    ├─ Tarea 3 → Coder (implementa endpoints)
    │           └─ Planning Agent actualiza plan
    └─ Tarea 4 → Coder (agrega tests)
                └─ Planning Agent → DELEGATE_TO_SUMMARY
    ↓
Summary Agent
    └─ Resumen completo de todo el proyecto
```

**Ejemplo**:
```
Usuario: "Create a REST API with FastAPI for user management"
  → Planning Agent: Crea plan de 6 pasos
  → Paso 1: CodeSearcher revisa proyecto
  → Paso 2: Coder crea models/user.py
  → Paso 3: Coder crea routes/users.py
  → Paso 4: Coder crea schemas/user.py
  → Paso 5: Coder agrega tests
  → Paso 6: Coder actualiza main.py
  → Summary: Lista todos los archivos creados
```

---

## 🧠 Sistema de Prompts

Todos los prompts están centralizados en `src/config/prompts.py`:

| Prompt | Agente | Propósito |
|--------|--------|-----------|
| `AGENT_SYSTEM_PROMPT` | Coder | Instrucciones para modificación de código |
| `CODE_SEARCHER_SYSTEM_MESSAGE` | CodeSearcher | Solo búsqueda y análisis |
| `PLANNING_AGENT_SYSTEM_MESSAGE` | Planning | Creación y gestión de planes |
| `SUMMARY_AGENT_SYSTEM_MESSAGE` | Summary | Resúmenes finales |
| `COMPLEXITY_DETECTOR_PROMPT` | Classifier | Detección SIMPLE vs COMPLEX |

---

## 📊 Gestión de Estado

### Historial de Conversación

```python
mensaje = {
    "role": "user" | "assistant" | "system",
    "content": "...",
    "timestamp": datetime,
    "metadata": {
        "tokens": int,
        "agent": str,
        "tool_calls": [...]
    }
}
```

### Compresión Automática

Cuando `len(messages) * avg_tokens > summary_threshold`:
1. Crea prompt de resumen
2. Summarizer Agent genera resumen conciso
3. Mantiene últimos 3 mensajes + resumen
4. Reduce significativamente el uso de tokens

---

## 🔌 Integración con AutoGen 0.4

CodeAgent utiliza AutoGen 0.4 con las siguientes características:

- **AssistantAgent**: Agentes con herramientas
- **SelectorGroupChat**: Orquestación de múltiples agentes
- **FunctionSchema**: Definición de herramientas
- **OpenAIChatCompletionClient**: Cliente LLM compatible

---

## 🎯 Principios de Diseño

1. **Modularidad**: Cada componente tiene una responsabilidad única
2. **Escalabilidad**: Fácil agregar nuevas herramientas y agentes
3. **Simplicidad**: Flujo SIMPLE para tareas cotidianas
4. **Planificación**: Flujo COMPLEX para proyectos grandes
5. **Memoria Persistente**: ChromaDB para contexto entre sesiones
6. **Observabilidad**: Langfuse para trazado y métricas

---

## 📚 Tecnologías Utilizadas

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **AutoGen** | >=0.4.0 | Framework de agentes |
| **ChromaDB** | >=0.4.0 | Base de datos vectorial |
| **Rich** | >=13.0.0 | Formateo de terminal |
| **Prompt Toolkit** | >=3.0.0 | CLI interactiva |
| **Pandas** | >=2.0.0 | Procesamiento de datos |
| **Langfuse** | >=2.0.0 | Observabilidad |
| **Python** | >=3.10 | Lenguaje base |

---

## 🔍 Ver También

- **[Herramientas y Características](Tools-and-Features)** - Catálogo completo de herramientas
- **[Sistema de Memoria](Memory-System)** - Detalles del sistema RAG
- **[Desarrollo](Development)** - Cómo contribuir al proyecto
- **[Evaluación SWE-bench](SWE-Bench-Evaluation)** - Benchmarking del agente

---

[← Volver al Home](Home) | [Herramientas →](Tools-and-Features)
