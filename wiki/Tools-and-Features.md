# 🛠️ Herramientas y Características - CodeAgent

CodeAgent incluye **45+ herramientas** integradas, organizadas en 6 categorías principales. Esta página documenta cada herramienta con ejemplos de uso.

## 📊 Resumen de Herramientas

| Categoría | Cantidad | Descripción |
|-----------|----------|-------------|
| [📁 Filesystem](#-filesystem-7-herramientas) | 7 | Operaciones de archivos y directorios |
| [🔀 Git](#-git-8-herramientas) | 8 | Control de versiones completo |
| [📊 JSON](#-json-8-herramientas) | 8 | Procesamiento y validación JSON |
| [📈 CSV](#-csv-7-herramientas) | 7 | Análisis y manipulación CSV |
| [🌐 Web](#-web-7-herramientas) | 7 | Wikipedia y búsqueda web |
| [🔍 Analysis](#-analysis-5-herramientas) | 5 | Análisis de código Python y búsqueda |
| [🧠 Memory](#-memory-8-herramientas) | 8 | Sistema RAG de memoria vectorial |

**Total**: **50 herramientas**

---

## 📁 Filesystem (7 herramientas)

### `read_file`
Lee el contenido de un archivo con soporte para rangos de líneas.

**Ejemplos**:
```bash
You: read the README.md file
You: read main.py lines 10 to 50
You: show me the content of config.py
```

### `write_file`
Crea o sobrescribe un archivo con contenido.

**Ejemplos**:
```bash
You: create a file utils.py with a function to validate emails
You: write a new config.json with the database settings
```

### `edit_file`
Edita archivos usando búsqueda y reemplazo quirúrgico.

**Ejemplos**:
```bash
You: @auth.py change the password hash algorithm to bcrypt
You: in config.py, update the database URL
You: fix the typo in line 45 of main.py
```

### `list_dir`
Lista el contenido de un directorio.

**Ejemplos**:
```bash
You: list files in the src/ directory
You: show me what's in the current directory
You: list all files in utils/
```

### `delete_file`
Elimina un archivo de forma segura.

**Ejemplos**:
```bash
You: delete the old_config.py file
You: remove test_old.py
```

### `file_search`
Búsqueda difusa de archivos por nombre.

**Ejemplos**:
```bash
You: find files with 'auth' in the name
You: search for config files
```

### `glob_search`
Búsqueda de archivos usando patrones glob.

**Ejemplos**:
```bash
You: find all Python files (*.py)
You: search for all JSON files in src/
You: list all test files (**/*test*.py)
```

---

## 🔀 Git (8 herramientas)

### `git_status`
Obtiene el estado del repositorio Git.

**Ejemplos**:
```bash
You: show git status
You: what files have changed?
```

### `git_add`
Agrega archivos al área de preparación.

**Ejemplos**:
```bash
You: git add main.py
You: stage all changes
You: add all Python files
```

### `git_commit`
Crea un commit con los cambios preparados.

**Ejemplos**:
```bash
You: commit with message "Added authentication"
You: create a commit for these changes
```

### `git_push`
Envía commits al repositorio remoto.

**Ejemplos**:
```bash
You: push changes to origin
You: git push to main branch
```

### `git_pull`
Obtiene cambios del repositorio remoto.

**Ejemplos**:
```bash
You: pull latest changes
You: git pull from origin
```

### `git_log`
Muestra el historial de commits.

**Ejemplos**:
```bash
You: show last 5 commits
You: git log with 10 entries
```

### `git_branch`
Gestiona ramas: listar, crear, eliminar, cambiar.

**Ejemplos**:
```bash
You: list all branches
You: create a new branch feature/auth
You: switch to main branch
You: delete branch old-feature
```

### `git_diff`
Muestra diferencias en el repositorio.

**Ejemplos**:
```bash
You: show git diff
You: what changed in staged files?
You: diff of working tree
```

---

## 📊 JSON (8 herramientas)

### `read_json`
Lee y parsea un archivo JSON.

**Ejemplos**:
```bash
You: read the package.json file
You: show me the content of config.json
```

### `write_json`
Escribe datos a un archivo JSON.

**Ejemplos**:
```bash
You: create a config.json with database settings
You: write user data to users.json
```

### `merge_json_files`
Combina dos archivos JSON en uno.

**Ejemplos**:
```bash
You: merge config1.json and config2.json into final_config.json
You: combine user data from two JSON files
```

### `validate_json`
Valida que un archivo contenga JSON válido.

**Ejemplos**:
```bash
You: validate the syntax of config.json
You: check if data.json is valid JSON
```

### `format_json`
Formatea un archivo JSON con indentación consistente.

**Ejemplos**:
```bash
You: format config.json with proper indentation
You: prettify the messy JSON file
```

### `json_get_value`
Obtiene un valor específico usando ruta de claves (dot notation).

**Ejemplos**:
```bash
You: get the value of user.name from config.json
You: extract database.host from settings.json
```

### `json_set_value`
Establece un valor específico usando ruta de claves.

**Ejemplos**:
```bash
You: set user.email to "test@example.com" in config.json
You: update database.port to 5432 in settings.json
```

### `json_to_text`
Convierte un archivo JSON a formato de texto legible.

**Ejemplos**:
```bash
You: convert config.json to readable text
You: show data.json in text format
```

---

## 📈 CSV (7 herramientas)

### `read_csv`
Lee un archivo CSV y muestra su contenido.

**Ejemplos**:
```bash
You: read the sales.csv file
You: show me the first 10 rows of data.csv
You: read customers.csv with semicolon delimiter
```

### `write_csv`
Escribe datos a un archivo CSV.

**Ejemplos**:
```bash
You: create a products.csv with columns: id, name, price
You: write sales data to output.csv
```

### `csv_info`
Obtiene información estadística sobre un archivo CSV.

**Ejemplos**:
```bash
You: show statistics for sales.csv
You: get column types and null values from data.csv
You: analyze the structure of customers.csv
```

### `filter_csv`
Filtra un CSV por valor de columna.

**Ejemplos**:
```bash
You: filter sales.csv where product="Laptop"
You: get all rows from customers.csv where country="USA"
You: find sales in data.csv where amount > 1000
```

### `merge_csv_files`
Combina dos archivos CSV.

**Ejemplos**:
```bash
You: merge sales_2023.csv and sales_2024.csv
You: join customers.csv and orders.csv on customer_id
You: concatenate all monthly reports
```

### `csv_to_json`
Convierte un archivo CSV a formato JSON.

**Ejemplos**:
```bash
You: convert sales.csv to sales.json
You: transform data.csv to JSON format
```

### `sort_csv`
Ordena un CSV por columna.

**Ejemplos**:
```bash
You: sort sales.csv by amount in descending order
You: order customers.csv by name alphabetically
```

---

## 🌐 Web (7 herramientas)

### `wiki_search`
Busca artículos de Wikipedia relacionados con una consulta.

**Ejemplos**:
```bash
You: search Wikipedia for "Python programming"
You: find articles about "machine learning"
```

### `wiki_summary`
Obtiene un resumen de un artículo de Wikipedia.

**Ejemplos**:
```bash
You: get a summary of the Python article on Wikipedia
You: show me a brief description of "FastAPI"
```

### `wiki_content`
Obtiene el contenido completo de un artículo.

**Ejemplos**:
```bash
You: get the full content of "Git" article
You: show me the complete Wikipedia page for "REST API"
```

### `wiki_page_info`
Obtiene información detallada sobre una página de Wikipedia.

**Ejemplos**:
```bash
You: get metadata for "Python programming" page
You: show categories and links for "Docker" article
```

### `wiki_random`
Obtiene títulos de páginas aleatorias de Wikipedia.

**Ejemplos**:
```bash
You: get 5 random Wikipedia pages
You: show me a random article
```

### `wiki_set_language`
Cambia el idioma para búsquedas de Wikipedia.

**Ejemplos**:
```bash
You: set Wikipedia language to Spanish
You: change wiki language to French (fr)
```

### `web_search`
Búsqueda general en la web.

**Ejemplos**:
```bash
You: search the web for "best Python frameworks 2024"
You: find information about "Docker deployment"
```

---

## 🔍 Analysis (5 herramientas)

### `analyze_python_file`
Analiza un archivo Python para extraer su estructura.

**Ejemplos**:
```bash
You: analyze the structure of main.py
You: show imports, classes, and functions in auth.py
```

**Salida**:
```python
# Imports:
- import os
- from fastapi import FastAPI

# Classes:
- UserModel (lines 10-25)
- AuthService (lines 30-50)

# Functions:
- validate_user(email, password) (lines 55-70)
- createtoken(user_id) (lines 75-85)
```

### `find_function_definition`
Encuentra y muestra la definición de una función específica.

**Ejemplos**:
```bash
You: find the definition of login_user in auth.py
You: show me the validate_email function
```

### `list_all_functions`
Lista todas las funciones en un archivo Python.

**Ejemplos**:
```bash
You: list all functions in utils.py
You: show me all methods in the services.py file
```

### `grep_search`
Búsqueda de texto con patrones (regex).

**Ejemplos**:
```bash
You: search for "def authenticate" in all Python files
You: find where "database_url" is used
You: grep for "TODO" comments in src/
```

### `run_terminal_cmd`
Ejecuta comandos de shell.

**Ejemplos**:
```bash
You: run pytest to test the application
You: execute npm install
You: run the Flask development server
```

---

## 🧠 Memory (8 herramientas)

Sistema RAG (Retrieval-Augmented Generation) con ChromaDB para memoria persistente.

### Herramientas de Consulta

#### `query_conversation_memory`
Busca en el historial de conversaciones pasadas.

**Ejemplos**:
```bash
You: what did we discuss about authentication last week?
You: find conversations about database optimization
```

#### `query_codebase_memory`
Busca en el código indexado del proyecto.

**Ejemplos**:
```bash
You: where did we implement caching logic?
You: find the authentication middleware code
```

#### `query_decision_memory`
Busca decisiones arquitectónicas registradas.

**Ejemplos**:
```bash
You: what was our decision about the database schema?
You: recall our choice for the API framework
```

#### `query_preferences_memory`
Busca preferencias de usuario.

**Ejemplos**:
```bash
You: what's my preferred coding style?
You: recall my framework preferences
```

#### `query_user_memory`
Busca información del usuario.

**Ejemplos**:
```bash
You: what's my name and role?
You: recall my expertise areas
```

### Herramientas de Guardado

#### `save_user_info`
Guarda información sobre el usuario.

**Ejemplos**:
```bash
You: remember that my name is Juan and I'm a backend developer
You: save that I work on microservices architecture
```

#### `save_decision`
Registra una decisión arquitectónica.

**Ejemplos**:
```bash
You: remember we decided to use PostgreSQL for the database
You: save our decision to implement JWT authentication
```

#### `save_preference`
Guarda una preferencia de usuario.

**Ejemplos**:
```bash
You: remember I prefer async/await over callbacks
You: save that I like using FastAPI over Flask
```

---

## 📎 Características Especiales

### File Mentions con @

Menciona archivos específicos para darles máxima prioridad en el contexto.

**Sintaxis**: `@<nombre_archivo>`

**Características**:
- Selector interactivo con navegación por teclado (↑↓)
- Búsqueda y filtrado en tiempo real
- Los archivos mencionados tienen **máxima prioridad**
- Soporta múltiples archivos en una sola consulta
- Excluye automáticamente archivos ocultos y binarios

**Ejemplos**:
```bash
You: @main.py explain how this file works
You: @config.py @.env update the database settings
You: @auth.py add docstrings to all functions
You: @src/agents/coder.py refactor to use async
```

**Más info**: Ver [File Mentions Guide](File-Mentions)

### Comando /search (CodeSearcher)

El comando `/search` invoca el agente **CodeSearcher** especializado.

**Uso**:
```bash
You: /search authentication function
You: /search where is TaskPlanner used
You: /search how does logging work
```

**CodeSearcher proporciona**:
- 📍 Archivos relevantes con ubicaciones exactas
- 🔧 Funciones encontradas con código completo
- 📦 Variables y constantes importantes
- 🔗 Dependencias entre componentes
- 💡 Recomendaciones de qué modificar

**Más info**: Ver [CodeSearcher Guide](CodeSearcher)

### Comando /index (Indexación de Proyecto)

Indexa tu proyecto en la memoria vectorial para búsquedas semánticas rápidas.

**Uso**:
```bash
You: /index

# Salida:
📚 Indexing project in vector memory...
✅ Indexing completed!
  • Indexed files: 45
  • Chunks created: 234
```

**Beneficios**:
- Búsqueda semántica instantánea
- El agente recuerda la estructura del proyecto
- Consultas más rápidas y precisas

**Más info**: Ver [Memory System](Memory-System)

---

## 🎯 Cómo Usar las Herramientas

### Forma Natural (Recomendado)

Simplemente describe lo que necesitas en lenguaje natural:

```bash
You: read the README.md file
You: create a new utils.py with email validation
You: show me the git status
You: search for "login" function in the codebase
```

El agente selecciona automáticamente las herramientas apropiadas.

### Forma Directa (Para usuarios avanzados)

También puedes ser más específico:

```bash
You: use read_file to show main.py lines 10-50
You: run git_status to check repository state
You: use analyze_python_file on auth.py
```

---

## 💡 Consejos de Uso

1. **Combina herramientas**: El agente puede usar múltiples herramientas en una sola tarea
   ```bash
   You: read auth.py, find the login function, and add error handling
   # Usa: read_file + find_function_definition + edit_file
   ```

2. **Usa /search antes de modificar**: Entiende el código primero
   ```bash
   You: /search authentication system
   # Luego: modify the auth logic
   ```

3. **Aprovecha la memoria**: El agente recuerda entre sesiones
   ```bash
   # Sesión 1
   You: /index
   
   # Sesión 2 (otro día)
   You: where did we put the caching logic?
   ``` 

4. **File mentions para precisión**: Usa @ cuando sabes qué archivo necesitas
   ```bash
   You: @config.py update database URL to localhost
   ```

---

## 📚 Ver También

- **[CodeSearcher](CodeSearcher)** - Agente de búsqueda especializado
- **[File Mentions](File-Mentions)** - Guía completa de menciones de archivos
- **[Memory System](Memory-System)** - Sistema de memoria RAG
- **[Usage Guide](Usage-Guide)** - Guía completa de uso
- **[Configuration](Configuration)** - Configuración de herramientas

---

[← Volver al Home](Home) | [Arquitectura →](Architecture)
