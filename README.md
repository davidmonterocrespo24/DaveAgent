# 🤖 DaveAgent - AI-Powered Coding Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AutoGen](https://img.shields.io/badge/powered%20by-AutoGen%200.4-orange.svg)](https://microsoft.github.io/autogen/)

DaveAgent es un asistente de codificación inteligente con IA que trabaja en tu directorio actual. Utiliza AutoGen 0.4 para orquestar agentes especializados que te ayudan con tareas de desarrollo.

## ✨ Características

- 🚀 **Comando CLI Global**: Usa `daveagent` desde cualquier directorio
- 📂 **Trabajo Contextual**: Opera en tu directorio actual automáticamente
- 🧠 **Memoria Vectorial con ChromaDB**: Recuerda conversaciones, código y decisiones entre sesiones
- 🔍 **CodeSearcher**: Agente especializado para buscar y analizar código
- 📎 **File Mentions con @**: Menciona archivos específicos con `@` para darles prioridad máxima en el contexto
- 🔧 **42 Herramientas Integradas**: Filesystem, Git, JSON, CSV, Wikipedia, y más
- 🤖 **Agentes Inteligentes**: Selección automática del agente apropiado
- 📊 **Logging Completo**: Sistema de logs detallado para debugging
- 🎨 **Interfaz Rica**: CLI con colores y formato usando Rich
- ⚡ **Visualización en Tiempo Real**: Ve los pensamientos y acciones del agente mientras trabaja

## 🎯 Casos de Uso

### Desarrollo de Software
```bash
cd mi-proyecto
daveagent

# Buscar código antes de modificar
Tu: /search sistema de autenticación actual

# Mencionar archivos específicos con @
Tu: @main.py fix the authentication bug in this file
Tu: @config.py @.env update the API configuration

# Modificar con contexto
Tu: crear un módulo de autenticación con JWT
Tu: refactorizar el código en services/ para usar async/await
Tu: buscar todos los TODOs en el proyecto
```

### Análisis de Datos
```bash
cd datos-proyecto
daveagent

Tu: leer el archivo ventas.csv y mostrar un resumen
Tu: combinar todos los CSV en la carpeta data/ en uno solo
Tu: convertir el JSON de configuración a CSV
```

### Operaciones Git
```bash
cd mi-repo
daveagent

Tu: hacer commit de los cambios con un mensaje descriptivo
Tu: mostrar el diff de los últimos 3 commits
Tu: crear una rama feature/nueva-funcionalidad
```

## 📦 Instalación

### Instalación desde PyPI (Próximamente)

**Cuando esté publicado en PyPI**:

```bash
pip install daveagent-ai
daveagent
```

### Instalación desde Código Fuente

```bash
# 1. Clona o descarga el proyecto
git clone https://github.com/DaveAgent-AI/daveagent.git
cd daveagent

# 2. Instala en modo desarrollo
pip install -e .

# 3. ¡Usa desde cualquier directorio!
daveagent
```

### Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Dependencias Principales

- `autogen-agentchat>=0.4.0` - Framework de agentes
- `autogen-ext[openai]>=0.4.0` - Extensiones de modelos
- `prompt-toolkit>=3.0.0` - Interfaz de línea de comandos
- `rich>=13.0.0` - Formato y colores
- `pandas>=2.0.0` - Procesamiento de datos

Ver [INSTALACION.md](INSTALACION.md) para instrucciones detalladas.

## 🚀 Uso

### Comando Básico

```bash
# Desde cualquier directorio
cd tu-proyecto
daveagent
```

### Opciones

```bash
# Modo debug (logs detallados)
daveagent --debug

# Ver versión
daveagent --version

# Ver ayuda
daveagent --help
```

### Comandos Internos

Dentro de DaveAgent, puedes usar estos comandos:

| Comando | Descripción |
|---------|-------------|
| `/help` | Muestra ayuda de comandos |
| `/search <consulta>` | 🔍 Busca y analiza código |
| `/index` | 🧠 Indexa el proyecto en memoria vectorial |
| `/memory` | 📊 Muestra estadísticas de memoria |
| `@<archivo>` | 📎 Menciona archivo específico con prioridad alta |
| `/debug` | Activa/desactiva modo debug |
| `/logs` | Muestra ubicación de logs |
| `/stats` | Muestra estadísticas |
| `/clear` | Limpia el historial |
| `/new` | Nueva conversación |
| `/exit` | Salir de DaveAgent |

#### 🔍 Comando /search

El comando `/search` invoca al agente **CodeSearcher** para buscar y analizar código:

```bash
Tu: /search función de autenticación
Tu: /search dónde se usa la clase TaskPlanner
Tu: /search cómo funciona el sistema de logging
```

**CodeSearcher te proporciona:**
- 📍 Archivos relevantes con ubicaciones exactas
- 🔧 Funciones encontradas con código completo
- 📦 Variables y constantes importantes
- 🔗 Dependencias entre componentes
- 💡 Recomendaciones de qué modificar

Ver [docs/CODESEARCHER_GUIDE.md](docs/CODESEARCHER_GUIDE.md) para más detalles.

#### 📎 File Mentions con @

Menciona archivos específicos en tu consulta usando `@`:

```bash
Tu: @main.py explain how this file works
Tu: @config.py @.env update the database connection settings
Tu: @src/agents/code_searcher.py add docstrings to all methods
```

**Características:**
- ✅ Selector interactivo con navegación por teclado (↑↓)
- ✅ Búsqueda y filtrado en tiempo real
- ✅ Los archivos mencionados tienen **prioridad máxima** en el contexto
- ✅ Soporta múltiples archivos en una sola consulta
- ✅ Excluye automáticamente archivos ocultos y binarios

Ver [docs/FILE_MENTIONS.md](docs/FILE_MENTIONS.md) y [examples/file_mentions_demo.md](examples/file_mentions_demo.md) para ejemplos detallados.

#### 🧠 Sistema de Memoria Vectorial

DaveAgent utiliza **ChromaDB** para mantener memoria persistente entre sesiones:

```bash
# Indexar tu proyecto una vez
Tu: /index
📚 Indexando proyecto en memoria vectorial...
✅ Indexación completada!
  • Archivos indexados: 45
  • Chunks creados: 234

# Ver estadísticas de memoria
Tu: /memory
🧠 Estadísticas de Memoria Vectorial

📚 Sistema de memoria activo con 4 colecciones:
  • Conversations: Historial de conversaciones
  • Codebase: Código fuente indexado
  • Decisions: Decisiones arquitectónicas
  • Preferences: Preferencias del usuario
```

**Beneficios de la Memoria:**
- 💬 **Conversaciones**: Recuerda interacciones previas y mantiene contexto
- 📝 **Código Base**: Búsquedas semánticas en tu código sin grep
- 🎯 **Decisiones**: Mantiene consistencia en decisiones arquitectónicas
- ⚙️ **Preferencias**: Aprende tu estilo de código preferido

**Los agentes usan memoria automáticamente:**
- **CodeSearcher**: Consulta código indexado para búsquedas más rápidas
- **Coder**: Recuerda soluciones previas y preferencias de estilo
- **PlanningAgent**: Mantiene consistencia con decisiones pasadas

Ver [docs/MEMORY_SYSTEM.md](docs/MEMORY_SYSTEM.md) para documentación completa y [examples/memory_usage_example.py](examples/memory_usage_example.py) para ejemplos de uso.

## 🛠️ Herramientas Disponibles

### Filesystem (6 tools)
- `read_file` - Leer archivos
- `write_file` - Escribir archivos
- `edit_file` - Editar archivos
- `list_dir` - Listar directorios
- `delete_file` - Eliminar archivos
- `file_search` - Buscar archivos

### Git (8 tools)
- `git_status` - Estado del repositorio
- `git_add` - Añadir archivos
- `git_commit` - Crear commits
- `git_push` - Subir cambios
- `git_pull` - Bajar cambios
- `git_log` - Ver historial
- `git_branch` - Gestionar ramas
- `git_diff` - Ver diferencias

### JSON (8 tools)
- `read_json` - Leer JSON
- `write_json` - Escribir JSON
- `merge_json_files` - Combinar JSONs
- `validate_json` - Validar JSON
- `format_json` - Formatear JSON
- `json_get_value` - Obtener valor
- `json_set_value` - Establecer valor
- `json_to_text` - Convertir a texto

### CSV (7 tools)
- `read_csv` - Leer CSV
- `write_csv` - Escribir CSV
- `csv_info` - Información del CSV
- `filter_csv` - Filtrar datos
- `merge_csv` - Combinar CSVs
- `csv_to_json` - Convertir a JSON
- `sort_csv` - Ordenar datos

### Web (6 tools)
- `wiki_search` - Buscar en Wikipedia
- `wiki_summary` - Resumen de artículo
- `wiki_content` - Contenido completo
- `wiki_page_info` - Información de página
- `wiki_random` - Artículo aleatorio
- `wiki_set_language` - Cambiar idioma

### Analysis (7 tools)
- `analyze_python_file` - Analizar código Python
- `find_function_definition` - Buscar definiciones
- `list_all_functions` - Listar funciones
- `codebase_search` - Buscar en código
- `grep_search` - Búsqueda con grep
- `run_terminal_cmd` - Ejecutar comandos
- `diff_history` - Ver diferencias

## 📖 Ejemplos

### Ejemplo 1: Usar CodeSearcher antes de modificar

```bash
cd mi-proyecto
daveagent

# Primero, buscar contexto
Tu: /search sistema de utilidades existente

# El agente muestra funciones, archivos y estructura actual
# Ahora modificar con contexto

Tu: crear un módulo utils.py con funciones para:
    - validar email
    - formatear fechas
    - calcular hash MD5
```

DaveAgent primero analiza el código existente y luego crea el archivo `mi-proyecto/utils.py` con las funciones solicitadas, evitando duplicados y manteniendo consistencia.

### Ejemplo 2: Analizar un Proyecto

```bash
cd proyecto-existente
daveagent

Tu: analiza la estructura del proyecto y dame un resumen
Tu: cuántas funciones hay en total?
Tu: encuentra todos los archivos que usan la librería requests
```

### Ejemplo 3: Operaciones con Datos

```bash
cd datos
daveagent

Tu: lee el archivo ventas.csv y muestra las 10 ventas más altas
Tu: crea un nuevo CSV con solo las ventas de 2024
Tu: convierte el archivo config.json a CSV
```

## 🐛 Debugging y Logs

### Ver Logs

```bash
# Iniciar con logs detallados
daveagent --debug

# Dentro de DaveAgent
Tu: /logs
📄 Archivo de logs: logs/daveagent_20250131_154022.log
```

### Ubicación de Logs

Los logs se guardan en:
```
logs/
└── daveagent_YYYYMMDD_HHMMSS.log
```

Cada archivo contiene logs detallados con formato:
```
2025-01-31 15:40:22 | DaveAgent | INFO | process_user_request:257 | 📝 Nueva solicitud...
```

Ver [LOGGING_GUIDE.md](LOGGING_GUIDE.md) para más detalles.

## 🏗️ Arquitectura

```
DaveAgent/
├── src/
│   ├── agents/          # Agentes especializados
│   │   ├── task_planner.py      # Planificación de tareas
│   │   ├── task_executor.py     # Ejecución de tareas
│   │   └── code_searcher.py     # 🔍 Búsqueda de código
│   ├── config/          # Configuración y prompts
│   ├── interfaces/      # CLI interface
│   ├── managers/        # Gestión de conversación
│   ├── tools/           # 42 herramientas
│   │   ├── filesystem/
│   │   ├── git/
│   │   ├── data/       # JSON, CSV
│   │   ├── web/        # Wikipedia
│   │   └── analysis/
│   ├── utils/          # Utilidades (logger)
│   └── cli.py          # Punto de entrada CLI
├── docs/               # Documentación
│   └── CODESEARCHER_GUIDE.md  # Guía de CodeSearcher
└── main.py             # Aplicación principal
```

## 🔧 Configuración

### API Key

DaveAgent usa DeepSeek por defecto. Para cambiar el modelo:

1. Edita `main.py`:
```python
self.model_client = OpenAIChatCompletionClient(
    model="gpt-4",  # Cambia aquí
    api_key="tu-api-key",
    # ...
)
```

2. O usa variables de entorno en `.daveagent/.env`:
```bash
DAVEAGENT_API_KEY=tu-api-key
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_BASE_URL=https://api.openai.com/v1
```

### Problemas de SSL (Redes Corporativas)

Si experimentas errores de certificado SSL:

1. **Método 1:** Variable de entorno en `.daveagent/.env`:
```bash
DAVEAGENT_SSL_VERIFY=false
```

2. **Método 2:** Argumento de línea de comandos:
```bash
daveagent --no-ssl-verify
# o
daveagent --ssl-verify=false
```

3. **Método 3:** Variable de entorno del sistema:
```bash
export DAVEAGENT_SSL_VERIFY=false  # Linux/macOS
set DAVEAGENT_SSL_VERIFY=false     # Windows
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Para contribuir:

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit tus cambios: `git commit -m 'Agrega nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

### Desarrollo

```bash
# Instalar con dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Formatear código
black src/

# Verificar tipos
mypy src/
```

## 📚 Documentación

### Guías de Usuario
- [Guía de Instalación](INSTALACION.md) - Instalación detallada
- [Guía de CodeSearcher](docs/CODESEARCHER_GUIDE.md) - 🔍 Búsqueda y análisis de código
- [Guía de File Mentions](docs/FILE_MENTIONS.md) - 📎 Mencionar archivos con @
- [Demo de File Mentions](examples/file_mentions_demo.md) - Ejemplos interactivos
- [Guía de Logging](LOGGING_GUIDE.md) - Sistema de logs
- [Visualización en Tiempo Real](VISUALIZACION_TIEMPO_REAL.md) - Ver pensamientos del agente
- [Cambios Realizados](CAMBIOS_REALIZADOS.md) - Historial de cambios
- [Mejoras Implementadas](MEJORAS_IMPLEMENTACION.md) - Análisis técnico

### Para Desarrolladores
- [Publicar en PyPI](PUBLICAR_PYPI.md) - Guía completa para publicar en PyPI
- [Inicio Rápido PyPI](INICIO_RAPIDO_PYPI.md) - Publicar en 10 minutos
- [Integración de Agentes](docs/TEAM_INTEGRATION.md) - Arquitectura del equipo de agentes


## 🧪 Evaluación con SWE-bench (Linux)

Para evaluar el rendimiento del agente usando el estándar **SWE-bench Verified**, hemos incluido un script automatizado que funciona en entornos Linux (o WSL2).

### Requisitos Previos
- Entorno Linux o WSL2
- Docker instalado y corriendo (necesario para el harness de evaluación)
- Python 3.10+

### Ejecución

El script `setup_and_run_linux.sh` automatiza todo el proceso:
1. Compila e instala el agente
2. Ejecuta inferencia sobre 10 tareas de prueba
3. Corre la evaluación oficial usando Docker

```bash
# 1. Dar permisos de ejecución
chmod +x setup_and_run_linux.sh

# 2. Ejecutar el script
./setup_and_run_linux.sh
```

**Nota:** La evaluación completa puede tomar tiempo dependiendo de la velocidad de tu conexión y CPU.

## 🐛 Problemas Conocidos

Ver [CAMBIOS_REALIZADOS.md](CAMBIOS_REALIZADOS.md) para problemas resueltos.

Si encuentras un problema:
1. Revisa los [issues existentes](https://github.com/yourusername/daveagent/issues)
2. Crea un nuevo issue con detalles

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [AutoGen](https://microsoft.github.io/autogen/) - Framework de agentes
- [Rich](https://rich.readthedocs.io/) - Formato de terminal
- [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/) - CLI interactiva

## 📞 Contacto

- Website: https://github.com/yourusername/daveagent
- Issues: https://github.com/yourusername/daveagent/issues
- Email: contact@daveagent.ai

---

Hecho con ❤️ usando [AutoGen 0.4](https://microsoft.github.io/autogen/)
