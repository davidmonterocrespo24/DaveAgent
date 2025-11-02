# 🔍 CodeSearcher - Guía Completa

## ¿Qué es CodeSearcher?

CodeSearcher es un agente especializado en **búsqueda y análisis de código**. Su objetivo es proporcionarte **contexto completo y detallado** sobre tu código base antes de hacer modificaciones, ayudándote a entender:

- Dónde se encuentran las funciones y clases
- Cómo funcionan los componentes existentes
- Qué archivos necesitas modificar
- Dependencias entre componentes
- Variables importantes y su uso
- Referencias cruzadas en el código

## ¿Cuándo usar CodeSearcher?

### ✅ Úsalo cuando:

1. **Antes de modificar funcionalidad existente**
   - "¿Dónde está implementada la autenticación?"
   - "¿Qué archivos necesito modificar para cambiar el sistema de login?"

2. **Para entender cómo funciona algo**
   - "¿Cómo funciona el procesamiento de archivos CSV?"
   - "¿Qué hace la función `process_user_request`?"

3. **Para encontrar referencias**
   - "¿Dónde se usa la clase `TaskPlanner`?"
   - "¿Qué funciones llaman a `analyze_python_file`?"

4. **Para mapear dependencias**
   - "¿Qué módulos importa el archivo main.py?"
   - "¿Qué herramientas usa el agente Coder?"

5. **Para obtener contexto antes de implementar**
   - "Necesito agregar logging, muéstrame cómo está implementado actualmente"
   - "Quiero crear un nuevo agente, muéstrame la estructura de los existentes"

### ❌ NO lo uses para:

- Modificar código (usa el agente Coder para eso)
- Ejecutar comandos
- Crear archivos nuevos
- Hacer commits

## Cómo usar CodeSearcher

### Sintaxis básica

```bash
/search <tu consulta en lenguaje natural>
```

### Ejemplos prácticos

#### 1. Buscar funcionalidad específica

```bash
/search función de autenticación
```

**Resultado esperado:**
- Archivos que contienen código de autenticación
- Nombres de funciones relacionadas con login/auth
- Código completo de las funciones
- Variables y constantes importantes (ej. SECRET_KEY)
- Recomendaciones de qué archivos modificar

#### 2. Encontrar uso de una clase

```bash
/search dónde se usa la clase TaskPlanner
```

**Resultado esperado:**
- Definición de la clase TaskPlanner
- Todos los archivos que importan TaskPlanner
- Cómo se instancia la clase
- Qué métodos se llaman
- Ejemplos de uso en el código

#### 3. Entender un componente

```bash
/search cómo funciona el sistema de logging
```

**Resultado esperado:**
- Archivos relacionados con logging
- Clase DaveAgentLogger y sus métodos
- Cómo se configura el logger
- Ejemplos de uso (logger.info, logger.debug, etc.)
- Ubicación de archivos de log

#### 4. Encontrar herramientas/funciones

```bash
/search herramientas disponibles para el agente Coder
```

**Resultado esperado:**
- Lista de herramientas (tools) disponibles
- Dónde se definen las herramientas
- Cómo se registran con el agente
- Ejemplos de uso de cada herramienta

#### 5. Mapear estructura del proyecto

```bash
/search estructura de los agentes en el proyecto
```

**Resultado esperado:**
- Directorio src/agents/
- Archivos de cada agente (TaskPlanner, CodeSearcher, etc.)
- Jerarquía de clases
- Cómo se importan y usan

## Formato de la respuesta

CodeSearcher proporciona respuestas estructuradas en el siguiente formato:

### 📍 Archivos Relevantes
Lista de archivos con ubicación exacta de líneas

```
- `main.py` (líneas 88-111): Configuración del agente Coder
- `src/agents/code_searcher.py` (líneas 10-131): Definición completa del CodeSearcher
```

### 🔧 Funciones Encontradas

Para cada función importante:

```markdown
#### Función: `search_code_context_stream`
- **Ubicación**: `src/agents/code_searcher.py:165`
- **Parámetros**: query: str
- **Retorna**: AsyncGenerator (mensajes en streaming)
- **Propósito**: Busca y analiza código en modo streaming para ver progreso en tiempo real

**Código**:
```python
async def search_code_context_stream(self, query: str):
    async for msg in self.searcher_agent.run_stream(task=query):
        yield msg
```

**Usado en**:
- `main.py:309` - Método _run_code_searcher
```

### 📦 Variables/Constantes Importantes

```markdown
- `search_tools`: Lista de herramientas de búsqueda y análisis
  - Ubicación: `main.py:122-129`
  - Incluye: codebase_search, grep_search, file_search, analyze_python_file, etc.
```

### 🔗 Dependencias

```markdown
**Importa:**
- autogen_agentchat.agents.AssistantAgent
- autogen_ext.models.openai.OpenAIChatCompletionClient

**Depende de:**
- model_client: Cliente del modelo LLM
- tools: Herramientas de búsqueda (grep_search, codebase_search, etc.)
```

### 💡 Recomendaciones

```markdown
**Para modificar la funcionalidad de búsqueda:**
1. Edita `src/agents/code_searcher.py` - lógica principal
2. Actualiza `main.py:122-129` - herramientas disponibles
3. Modifica `main.py:295-368` - integración con CLI

**Ten en cuenta:**
- El agente usa streaming para mostrar progreso en tiempo real
- Máximo 10 iteraciones de herramientas (max_tool_iterations=10)
- Respuestas en formato Markdown estructurado
```

### 📝 Código Relevante Completo

Fragmentos completos de código contextualizados y listos para usar

## Visualización en tiempo real

Cuando ejecutas `/search`, verás en tiempo real:

1. **💭 Pensamientos del agente**
   ```
   💭 CodeSearcher: Voy a buscar primero con grep_search para encontrar referencias...
   ```

2. **🔧 Herramientas que usa**
   ```
   🔧 Buscando con: grep_search
   🔧 Buscando con: analyze_python_file
   🔧 Buscando con: read_file
   ```

3. **✅ Resultados de herramientas**
   ```
   ✅ CodeSearcher > grep_search: Found 15 occurrences in 8 files...
   ✅ CodeSearcher > read_file: Successfully read main.py (553 lines)...
   ```

4. **💬 Análisis completo final**
   El informe estructurado completo con toda la información encontrada

## Flujo de trabajo recomendado

### Antes de modificar código:

```bash
# 1. Busca contexto con CodeSearcher
/search sistema de logging actual

# 2. Lee el análisis proporcionado
# (CodeSearcher te mostrará archivos, funciones, variables, etc.)

# 3. Haz tu solicitud de modificación con contexto
Agrega un nuevo nivel de logging llamado TRACE que sea más detallado que DEBUG.
Basándome en el análisis anterior, necesito modificar src/utils/logger.py
para agregar el nivel TRACE y actualizar la configuración.
```

### Para proyectos nuevos:

```bash
# 1. Explora la estructura
/search estructura general del proyecto

# 2. Entiende componentes clave
/search cómo funcionan los agentes

# 3. Busca ejemplos similares
/search implementaciones de agentes existentes

# 4. Implementa tu funcionalidad
Crear un nuevo agente llamado "DocumentationAgent" siguiendo el patrón
de TaskPlanner y CodeSearcher...
```

## Herramientas que usa CodeSearcher

CodeSearcher tiene acceso a las siguientes herramientas especializadas:

### 🔎 Búsqueda
- **`codebase_search`**: Búsqueda inteligente en toda la base de código
- **`grep_search`**: Búsqueda por patrones/regex
- **`file_search`**: Búsqueda de archivos por nombre

### 📖 Lectura
- **`read_file`**: Lee archivos completos
- **`list_dir`**: Lista contenidos de directorios

### 🐍 Análisis Python
- **`analyze_python_file`**: Análisis detallado de archivos Python (funciones, clases, imports)
- **`find_function_definition`**: Encuentra definición exacta de una función
- **`list_all_functions`**: Lista todas las funciones en un archivo

## Configuración avanzada

### Modificar el system message

Para cambiar el comportamiento de CodeSearcher, edita el `system_message` en:

**Archivo:** `src/agents/code_searcher.py:40-125`

### Agregar más herramientas

Para darle acceso a más herramientas, modifica:

**Archivo:** `main.py:122-129`

```python
search_tools = [
    # Herramientas de búsqueda
    codebase_search, grep_search, file_search,
    # Herramientas de lectura
    read_file, list_dir,
    # Herramientas de análisis Python
    analyze_python_file, find_function_definition, list_all_functions,
    # NUEVAS HERRAMIENTAS AQUÍ
]
```

### Ajustar iteraciones máximas

En `src/agents/code_searcher.py:129`:

```python
max_tool_iterations=10,  # Aumenta para búsquedas más exhaustivas
```

## Tips y mejores prácticas

### 🎯 Sé específico en tus consultas

**❌ Malo:**
```bash
/search código
```

**✅ Bueno:**
```bash
/search función que procesa solicitudes del usuario en main.py
```

### 🔍 Usa lenguaje natural

CodeSearcher entiende español natural:

```bash
/search muéstrame cómo se configura el modelo de IA
/search dónde se definen las herramientas de Git
/search qué archivos necesito cambiar para modificar la interfaz CLI
```

### 📚 Combina múltiples búsquedas

Para proyectos complejos, usa varias búsquedas:

```bash
/search estructura de los agentes
# Espera resultado...

/search herramientas disponibles
# Espera resultado...

/search sistema de mensajería entre agentes
# Ahora tienes contexto completo
```

### 💾 Guarda el análisis

Si el análisis es valioso, guarda la sesión:

```bash
/save analisis_proyecto.txt
```

## Solución de problemas

### "No se encontraron resultados"

- Verifica que estás en el directorio correcto
- Usa términos más generales
- Revisa la ortografía

### "Demasiados resultados"

- Sé más específico en la consulta
- Usa nombres exactos de funciones/clases
- Especifica el archivo si lo conoces

### El agente se demora mucho

- El agente está siendo exhaustivo
- Puedes usar Ctrl+C para interrumpir
- Reduce el alcance de la búsqueda

## Ejemplos completos de uso

### Ejemplo 1: Agregar nueva funcionalidad

**Objetivo:** Agregar soporte para búsqueda de archivos JavaScript

```bash
# Paso 1: Entender cómo funciona actualmente
/search herramienta analyze_python_file

# Paso 2: Buscar estructura de herramientas
/search cómo se registran las herramientas en los agentes

# Paso 3: Con el contexto, solicitar la implementación
Crea una nueva herramienta llamada analyze_javascript_file similar a
analyze_python_file que extraiga funciones, clases y exports de archivos .js
```

### Ejemplo 2: Debugging

**Objetivo:** Entender por qué el agente no responde

```bash
# Buscar flujo de ejecución
/search función process_user_request

# Ver sistema de mensajes
/search tipos de mensajes ThoughtEvent ToolCallRequestEvent

# Ver manejo de errores
/search manejo de excepciones en main.py
```

### Ejemplo 3: Refactorización

**Objetivo:** Separar el código de CLI en módulos más pequeños

```bash
# Analizar estructura actual
/search clase CLIInterface

# Ver dependencias
/search qué usa CLIInterface

# Planificar refactorización
/search métodos de print_ en CLIInterface

# Ahora puedes pedir: "Separa los métodos print_* en módulos temáticos"
```

## Integración con workflow completo

CodeSearcher está diseñado para trabajar en conjunto con el agente Coder:

```
┌─────────────────────────────────────────────────────────┐
│  1. 🔍 /search: Analiza el código existente             │
│     - Encuentra funciones relevantes                    │
│     - Identifica archivos a modificar                   │
│     - Obtiene contexto completo                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. 💬 Solicitud normal: Modifica el código             │
│     - Usa la información de CodeSearcher                │
│     - El agente Coder hace los cambios                  │
│     - Se ejecutan en tiempo real                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. ✅ Verificación: Confirma los cambios               │
│     - Revisa archivos modificados                       │
│     - Ejecuta tests si es necesario                     │
│     - Commit con Git                                    │
└─────────────────────────────────────────────────────────┘
```
DEE
## Preguntas frecuentes

### ¿CodeSearcher modifica código?

**No.** CodeSearcher es un agente de **solo lectura**. Su única función es analizar y proporcionar información. No modifica archivos, no ejecuta comandos, y no hace commits.

### ¿Puedo usar CodeSearcher en cualquier lenguaje?

CodeSearcher puede buscar en **cualquier tipo de archivo** (JavaScript, Python, Java, etc.), pero el análisis detallado (estructura de funciones, clases) solo funciona completamente para **Python** usando `analyze_python_file`.

Para otros lenguajes, obtendrás:
- Contenido de archivos
- Búsquedas grep/regex
- Referencias cruzadas

### ¿CodeSearcher consume muchos tokens?

CodeSearcher puede hacer múltiples llamadas a herramientas (hasta 10 iteraciones), lo que consume tokens. Sin embargo:
- Solo analiza archivos relevantes
- Proporciona valor agregado (ahorra tiempo y errores)
- Puedes limitar el alcance siendo específico en la consulta

### ¿Puedo usar CodeSearcher en proyectos grandes?

**Sí**, pero considera:
- Sé específico en las búsquedas
- Busca por módulos/directorios específicos
- Divide búsquedas complejas en varias consultas más pequeñas

---

## Conclusión

CodeSearcher es una herramienta poderosa que te ayuda a:

✅ **Entender** el código existente antes de modificarlo
✅ **Encontrar** funciones, clases y dependencias rápidamente
✅ **Planificar** cambios con contexto completo
✅ **Evitar errores** al conocer el impacto de tus modificaciones
✅ **Ahorrar tiempo** al tener toda la información en un solo lugar

**¡Úsalo antes de cada modificación importante para trabajar con confianza!** 🚀
