# Estructura del Proyecto DaveAgent

## 📁 Nueva Organización por Responsabilidades

```
DaveAgent/
├── src/                          # Código fuente principal
│   ├── __init__.py
│   │
│   ├── agents/                   # 🤖 Agentes del sistema
│   │   ├── __init__.py
│   │   ├── task_planner.py       # Agente planificador de tareas
│   │   └── task_executor.py      # Agente ejecutor de tareas
│   │
│   ├── managers/                 # 📊 Gestores del sistema
│   │   ├── __init__.py
│   │   └── conversation_manager.py  # Gestión de conversación e historial
│   │
│   ├── interfaces/               # 🖥️ Interfaces de usuario
│   │   ├── __init__.py
│   │   └── cli_interface.py      # Interfaz CLI con Rich
│   │
│   ├── config/                   # ⚙️ Configuración
│   │   ├── __init__.py
│   │   └── prompt.py             # Prompts del sistema
│   │
│   └── tools/                    # 🛠️ Herramientas del agente
│       ├── __init__.py           # Exporta todas las herramientas
│       │
│       ├── filesystem/           # 📁 Operaciones de archivos
│       │   ├── __init__.py
│       │   └── file_operations.py
│       │       ├── read_file()
│       │       ├── write_file()
│       │       ├── list_dir()
│       │       ├── edit_file()
│       │       ├── delete_file()
│       │       └── file_search()
│       │
│       ├── git/                  # 🔀 Operaciones Git
│       │   ├── __init__.py
│       │   └── git_operations.py
│       │       ├── git_status()
│       │       ├── git_add()
│       │       ├── git_commit()
│       │       ├── git_push()
│       │       ├── git_pull()
│       │       ├── git_log()
│       │       ├── git_branch()
│       │       └── git_diff()
│       │
│       ├── data/                 # 📊 Procesamiento de datos
│       │   ├── __init__.py
│       │   ├── json_tools.py
│       │   │   ├── read_json()
│       │   │   ├── write_json()
│       │   │   ├── merge_json_files()
│       │   │   ├── validate_json()
│       │   │   ├── format_json()
│       │   │   ├── json_get_value()
│       │   │   ├── json_set_value()
│       │   │   └── json_to_text()
│       │   │
│       │   └── csv_tools.py
│       │       ├── read_csv()
│       │       ├── write_csv()
│       │       ├── csv_info()
│       │       ├── filter_csv()
│       │       ├── merge_csv()
│       │       ├── csv_to_json()
│       │       └── sort_csv()
│       │
│       ├── web/                  # 🌐 Herramientas web
│       │   ├── __init__.py
│       │   └── wikipedia_tools.py
│       │       ├── wiki_search()
│       │       ├── wiki_summary()
│       │       ├── wiki_content()
│       │       ├── wiki_page_info()
│       │       ├── wiki_random()
│       │       └── wiki_set_language()
│       │
│       └── analysis/             # 🔍 Análisis y búsqueda
│           ├── __init__.py
│           ├── code_analyzer.py
│           │   ├── analyze_python_file()
│           │   ├── find_function_definition()
│           │   └── list_all_functions()
│           │
│           └── search_tools.py
│               ├── grep_search()
│               ├── codebase_search()
│               ├── run_terminal_cmd()│               
│
├── main_new.py                   # 🚀 Punto de entrada con nueva estructura
├── main.py                       # (Versión anterior)
├── requirements.txt              # 📦 Dependencias
└── README.md                     # 📖 Documentación

# Archivos antiguos (pueden eliminarse después de migración)
├── tools/                        # Versión antigua sin organizar
├── task_planner.py              # Movido a src/agents/
├── task_executor.py             # Movido a src/agents/
├── conversation_manager.py      # Movido a src/managers/
├── cli_interface.py             # Movido a src/interfaces/
└── prompt.py                    # Movido a src/config/
```

## 🎯 Responsabilidades por Módulo

### 1. **src/agents/** - Agentes Inteligentes
- **task_planner.py**: Crea y actualiza planes de ejecución estructurados
- **task_executor.py**: Ejecuta tareas usando el coder_agent

### 2. **src/managers/** - Gestión de Estado
- **conversation_manager.py**: Maneja historial de conversación, compresión automática, estadísticas

### 3. **src/interfaces/** - Interfaces de Usuario
- **cli_interface.py**: CLI con Rich (banners, colores, prompts, mensajes)

### 4. **src/config/** - Configuración
- **prompt.py**: Prompts del sistema para los agentes

### 5. **src/tools/** - Herramientas Especializadas

#### 📁 Filesystem (6 herramientas)
- Operaciones básicas de archivos
- Todas async, sin decoradores

#### 🔀 Git (8 herramientas)
- Operaciones completas de Git
- Status, commit, push, pull, log, branch, diff

#### 📊 Data (15 herramientas)
- **JSON** (8): Lectura, escritura, validación, transformación
- **CSV** (7): Lectura, escritura, filtrado, análisis, conversión

#### 🌐 Web (6 herramientas)
- Wikipedia: Búsqueda, resúmenes, contenido completo

#### 🔍 Analysis (7 herramientas)
- **Code Analyzer** (3): Análisis de código Python, búsqueda de funciones
- **Search Tools** (4): grep, búsqueda de código, comandos terminal, diff

## 📊 Estadísticas

- **Total de herramientas**: 42
- **Agentes**: 2 (Planner, Coder)
- **Gestores**: 1 (ConversationManager)
- **Interfaces**: 1 (CLI)

## 🔧 Cómo Usar

### Opción 1: Nueva estructura (recomendado)
```bash
python main_new.py
```

### Opción 2: Estructura antigua (compatibilidad)
```bash
python main.py
```

## 🚀 Ventajas de la Nueva Estructura

1. **Organización Clara**: Cada módulo tiene una responsabilidad bien definida
2. **Fácil Mantenimiento**: Archivos agrupados por funcionalidad
3. **Escalabilidad**: Fácil agregar nuevas herramientas en su categoría
4. **Imports Limpios**: Importaciones jerárquicas y organizadas
5. **Separación de Concerns**: Agentes, gestores, interfaces, herramientas separados

## 📝 Migración desde Estructura Antigua

1. Todos los imports de `tools` ahora son `from src.tools import ...`
2. Los agentes están en `from src.agents import ...`
3. Los managers en `from src.managers import ...`
4. Las interfaces en `from src.interfaces import ...`
5. La configuración en `from src.config import ...`

## 🔄 Siguiente Paso

Una vez verificado que `main_new.py` funciona correctamente:

```bash
# Respaldar versión antigua
mv main.py main_old.py

# Renombrar nueva versión
mv main_new.py main.py

# Opcional: Limpiar archivos antiguos
rm -rf tools/ (después de verificar)
rm task_planner.py task_executor.py conversation_manager.py cli_interface.py prompt.py
```
