# 🤖 CodeAgent - AI-Powered Coding Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AutoGen](https://img.shields.io/badge/powered%20by-AutoGen%200.4-orange.svg)](https://microsoft.github.io/autogen/)

CodeAgent es un asistente de codificación inteligente con IA que trabaja en tu directorio actual. Utiliza AutoGen 0.4 para orquestar agentes especializados que te ayudan con tareas de desarrollo.

## ✨ Características

- 🚀 **Comando CLI Global**: Usa `codeagent` desde cualquier directorio
- 📂 **Trabajo Contextual**: Opera en tu directorio actual automáticamente
- 🔍 **CodeSearcher**: Agente especializado para buscar y analizar código
- 🔧 **42 Herramientas Integradas**: Filesystem, Git, JSON, CSV, Wikipedia, y más
- 🤖 **Agentes Inteligentes**: Selección automática del agente apropiado
- 📊 **Logging Completo**: Sistema de logs detallado para debugging
- 🎨 **Interfaz Rica**: CLI con colores y formato usando Rich
- ⚡ **Visualización en Tiempo Real**: Ve los pensamientos y acciones del agente mientras trabaja

## 🎯 Casos de Uso

### Desarrollo de Software
```bash
cd mi-proyecto
codeagent

# Buscar código antes de modificar
Tu: /search sistema de autenticación actual

# Modificar con contexto
Tu: crear un módulo de autenticación con JWT
Tu: refactorizar el código en services/ para usar async/await
Tu: buscar todos los TODOs en el proyecto
```

### Análisis de Datos
```bash
cd datos-proyecto
codeagent

Tu: leer el archivo ventas.csv y mostrar un resumen
Tu: combinar todos los CSV en la carpeta data/ en uno solo
Tu: convertir el JSON de configuración a CSV
```

### Operaciones Git
```bash
cd mi-repo
codeagent

Tu: hacer commit de los cambios con un mensaje descriptivo
Tu: mostrar el diff de los últimos 3 commits
Tu: crear una rama feature/nueva-funcionalidad
```

## 📦 Instalación

### Instalación desde PyPI (Próximamente)

**Cuando esté publicado en PyPI**:

```bash
pip install codeagent-ai
codeagent
```

### Instalación desde Código Fuente

```bash
# 1. Clona o descarga el proyecto
git clone https://github.com/CodeAgent-AI/codeagent.git
cd codeagent

# 2. Instala en modo desarrollo
pip install -e .

# 3. ¡Usa desde cualquier directorio!
codeagent
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
codeagent
```

### Opciones

```bash
# Modo debug (logs detallados)
codeagent --debug

# Ver versión
codeagent --version

# Ver ayuda
codeagent --help
```

### Comandos Internos

Dentro de CodeAgent, puedes usar estos comandos:

| Comando | Descripción |
|---------|-------------|
| `/help` | Muestra ayuda de comandos |
| `/search <consulta>` | 🔍 Busca y analiza código (nuevo) |
| `/debug` | Activa/desactiva modo debug |
| `/logs` | Muestra ubicación de logs |
| `/stats` | Muestra estadísticas |
| `/clear` | Limpia el historial |
| `/new` | Nueva conversación |
| `/exit` | Salir de CodeAgent |

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
codeagent

# Primero, buscar contexto
Tu: /search sistema de utilidades existente

# El agente muestra funciones, archivos y estructura actual
# Ahora modificar con contexto

Tu: crear un módulo utils.py con funciones para:
    - validar email
    - formatear fechas
    - calcular hash MD5
```

CodeAgent primero analiza el código existente y luego crea el archivo `mi-proyecto/utils.py` con las funciones solicitadas, evitando duplicados y manteniendo consistencia.

### Ejemplo 2: Analizar un Proyecto

```bash
cd proyecto-existente
codeagent

Tu: analiza la estructura del proyecto y dame un resumen
Tu: cuántas funciones hay en total?
Tu: encuentra todos los archivos que usan la librería requests
```

### Ejemplo 3: Operaciones con Datos

```bash
cd datos
codeagent

Tu: lee el archivo ventas.csv y muestra las 10 ventas más altas
Tu: crea un nuevo CSV con solo las ventas de 2024
Tu: convierte el archivo config.json a CSV
```

## 🐛 Debugging y Logs

### Ver Logs

```bash
# Iniciar con logs detallados
codeagent --debug

# Dentro de CodeAgent
Tu: /logs
📄 Archivo de logs: logs/codeagent_20250131_154022.log
```

### Ubicación de Logs

Los logs se guardan en:
```
logs/
└── codeagent_YYYYMMDD_HHMMSS.log
```

Cada archivo contiene logs detallados con formato:
```
2025-01-31 15:40:22 | CodeAgent | INFO | process_user_request:257 | 📝 Nueva solicitud...
```

Ver [LOGGING_GUIDE.md](LOGGING_GUIDE.md) para más detalles.

## 🏗️ Arquitectura

```
CodeAgent/
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

CodeAgent usa DeepSeek por defecto. Para cambiar el modelo:

1. Edita `main.py`:
```python
self.model_client = OpenAIChatCompletionClient(
    model="gpt-4",  # Cambia aquí
    api_key="tu-api-key",
    # ...
)
```

2. O usa variables de entorno:
```bash
export OPENAI_API_KEY="tu-api-key"
export OPENAI_MODEL="gpt-4"
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
- [Guía de Logging](LOGGING_GUIDE.md) - Sistema de logs
- [Visualización en Tiempo Real](VISUALIZACION_TIEMPO_REAL.md) - Ver pensamientos del agente
- [Cambios Realizados](CAMBIOS_REALIZADOS.md) - Historial de cambios
- [Mejoras Implementadas](MEJORAS_IMPLEMENTACION.md) - Análisis técnico

### Para Desarrolladores
- [Publicar en PyPI](PUBLICAR_PYPI.md) - Guía completa para publicar en PyPI
- [Inicio Rápido PyPI](INICIO_RAPIDO_PYPI.md) - Publicar en 10 minutos
- [Integración de Agentes](docs/TEAM_INTEGRATION.md) - Arquitectura del equipo de agentes

## 🐛 Problemas Conocidos

Ver [CAMBIOS_REALIZADOS.md](CAMBIOS_REALIZADOS.md) para problemas resueltos.

Si encuentras un problema:
1. Revisa los [issues existentes](https://github.com/yourusername/codeagent/issues)
2. Crea un nuevo issue con detalles

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [AutoGen](https://microsoft.github.io/autogen/) - Framework de agentes
- [Rich](https://rich.readthedocs.io/) - Formato de terminal
- [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/) - CLI interactiva

## 📞 Contacto

- Website: https://github.com/yourusername/codeagent
- Issues: https://github.com/yourusername/codeagent/issues
- Email: contact@codeagent.ai

---

Hecho con ❤️ usando [AutoGen 0.4](https://microsoft.github.io/autogen/)
