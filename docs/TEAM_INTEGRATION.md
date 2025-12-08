# 🤖 Integración del Team de Agentes

## Resumen

DaveAgent ahora utiliza un **SelectorGroupChat** con 3 agentes especializados que trabajan en conjunto de manera inteligente. El sistema selecciona automáticamente el agente más apropiado según la tarea solicitada.

## Arquitectura del Team

```
SelectorGroupChat
├── CodeSearcher    (Búsqueda y análisis)
├── Planner         (Planificación compleja)
└── Coder           (Ejecución simple)
```

### 1. CodeSearcher 🔍

**Propósito**: Búsqueda y análisis de código

**Cuándo se usa**:
- Entender cómo funciona código existente ANTES de modificarlo
- Encontrar dónde está implementada una funcionalidad
- Buscar referencias a funciones, clases o variables
- Analizar dependencias entre archivos
- Obtener contexto completo sobre una característica
- Mapear la estructura de un proyecto o módulo

**Señales clave**:
- "dónde está", "cómo funciona", "busca", "encuentra", "analiza"
- "muéstrame", "referencias a", "explicame cómo"
- "antes de modificar", "quiero entender", "necesito contexto"

**Herramientas disponibles**:
- `codebase_search` - Búsqueda inteligente en todo el código
- `grep_search` - Búsqueda por patrones/regex
- `file_search` - Búsqueda de archivos por nombre
- `read_file` - Lectura de archivos completos
- `list_dir` - Listar directorios
- `analyze_python_file` - Análisis detallado de archivos Python
- `find_function_definition` - Localizar definiciones de funciones
- `list_all_functions` - Listar todas las funciones

**Ejemplo de uso**:
```
Usuario: "dónde está implementado el sistema de logging?"

Sistema selecciona: CodeSearcher
↓
CodeSearcher busca en el código con:
1. grep_search("logger")
2. analyze_python_file("src/utils/logger.py")
3. read_file("main.py") para ver cómo se usa

Resultado: Análisis completo con:
- Archivos relevantes (src/utils/logger.py, main.py)
- Clase DaveAgentLogger con código completo
- Métodos disponibles (debug, info, warning, error)
- Ejemplos de uso en el código
- Recomendaciones de modificación
```

### 2. Planner 📋

**Propósito**: Planificación de tareas complejas

**Cuándo se usa**:
- Múltiples archivos o componentes
- Sistemas completos o aplicaciones
- Refactorización mayor
- Arquitectura o diseño de soluciones
- Proyectos que necesitan planificación estructurada

**Señales clave**:
- "sistema", "aplicación", "proyecto completo"
- "múltiples archivos", "crear desde cero", "refactorizar todo"

**Ejemplo de uso**:
```
Usuario: "crea un sistema completo de autenticación con JWT"

Sistema selecciona: Planner
↓
Planner crea un plan:
1. Crear modelo de usuario (models/user.py)
2. Implementar generación de tokens JWT (auth/jwt.py)
3. Crear middleware de autenticación (middleware/auth.py)
4. Agregar rutas de login/logout (routes/auth.py)
5. Tests unitarios

Luego delega cada tarea al Coder para ejecución
```

### 3. Coder 💻

**Propósito**: Ejecución de tareas simples y directas

**Cuándo se usa**:
- Leer o buscar archivos específicos
- Editar 1-3 archivos
- Corregir un bug puntual
- Agregar una función simple
- Ejecutar comandos del sistema
- Operaciones Git
- Trabajar con JSON/CSV
- Tareas de 1-3 pasos

**Señales clave**:
- "crea", "modifica", "corrige este error"
- "agrega esta función", "ejecuta", "pequeño cambio"
- "git status", "escribe"

**Herramientas disponibles**: Todas (45+ herramientas)

**Ejemplo de uso**:
```
Usuario: "lee el archivo config.json"

Sistema selecciona: Coder
↓
Coder ejecuta: read_file("config.json")
```

## Flujo de Trabajo Inteligente

### Para MODIFICACIONES a código existente:

```
1. CodeSearcher → obtiene contexto completo del código existente
2. Planner o Coder → hace la modificación con el contexto obtenido
```

**Ejemplo**:
```bash
Usuario: "modifica la función process_user_request para agregar logging"

Flujo automático:
1. CodeSearcher busca y analiza process_user_request
   - Ubicación: main.py:401
   - Código completo de la función
   - Dependencias (logger, cli, conversation_manager)
   - Cómo se usa el logger actualmente

2. Coder modifica la función con el contexto
   - Agrega logging adicional
   - Mantiene consistencia con logging existente
   - Actualiza la función
```

### Para BÚSQUEDAS y ANÁLISIS:

```
CodeSearcher directamente
```

**Ejemplo**:
```bash
Usuario: "analiza cómo funciona el sistema de streaming"

Sistema selecciona: CodeSearcher
↓
Proporciona análisis completo sin modificar nada
```

### Para CREACIÓN de código nuevo:

```
- Planner (si es complejo)
- Coder (si es simple)
```

**Ejemplo complejo**:
```bash
Usuario: "crea una API REST completa con FastAPI"
→ Planner crea plan estructurado
→ Delega tareas al Coder
```

**Ejemplo simple**:
```bash
Usuario: "crea una función que sume dos números"
→ Coder crea la función directamente
```

### Para TAREAS SIMPLES sin modificación:

```
Coder directamente
```

**Ejemplo**:
```bash
Usuario: "git status"
→ Coder ejecuta el comando
```

## Implementación Técnica

### Configuración en main.py

```python
def _setup_team(self):
    """Configura el equipo de agentes con SelectorGroupChat"""

    # Prompt de selección inteligente
    selector_prompt = """
    Selecciona el agente más apropiado:

    1. CodeSearcher - Para búsqueda y análisis
    2. Planner - Para tareas complejas
    3. Coder - Para tareas simples

    {roles}
    {history}
    """

    # Crear el team con los 3 agentes
    self.team = SelectorGroupChat(
        participants=[
            self.code_searcher.searcher_agent,  # 🔍 Búsqueda
            self.planner.planner_agent,          # 📋 Planificación
            self.coder_agent                     # 💻 Ejecución
        ],
        model_client=self.model_client,
        termination_condition=termination,
        selector_prompt=selector_prompt,
    )
```

### Procesamiento de solicitudes

```python
async def process_user_request(self, user_input: str):
    """
    Procesa solicitud usando el equipo de agentes
    El selector elige automáticamente el mejor agente
    """

    # Usar streaming del TEAM para selección inteligente
    async for msg in self.team.run_stream(task=user_input):
        # Mostrar progreso en tiempo real
        # El selector elige el agente apropiado automáticamente
        # Visualizar pensamientos, herramientas y resultados
```

## Ventajas de la Integración

### 1. Selección Automática Inteligente ✅

El usuario no necesita especificar qué agente usar. El sistema lo determina automáticamente basándose en:
- Palabras clave en la solicitud
- Contexto de la conversación
- Complejidad de la tarea

### 2. Flujo de Trabajo Optimizado ⚡

**Antes** (manual):
```bash
/search función de login
# Usuario lee el análisis...
# Usuario escribe nueva solicitud con contexto...
modifica la función de login para agregar 2FA
```

**Ahora** (automático):
```bash
modifica la función de login para agregar 2FA
# Sistema automáticamente:
# 1. CodeSearcher busca y analiza login
# 2. Coder modifica con el contexto
```

### 3. Mejor Contexto para Modificaciones 🎯

Cuando el sistema detecta que vas a modificar código existente, automáticamente:
1. Primero busca con CodeSearcher
2. Obtiene contexto completo
3. Luego pasa al Coder/Planner con toda la información

Resultado: Modificaciones más precisas y menos errores.

### 4. Visualización en Tiempo Real 👀

Ves exactamente qué está haciendo el sistema:

```
🤖 Analizando solicitud y seleccionando el mejor agente...
💭 CodeSearcher: Voy a buscar información sobre la función login...
🔧 Buscando con: grep_search
✅ CodeSearcher > grep_search: Found 5 occurrences...
🔧 Buscando con: read_file
✅ CodeSearcher > read_file: Successfully read auth.py...
💬 [Análisis completo de CodeSearcher]

💭 Coder: Basándome en el análisis, voy a modificar auth.py...
🔧 Llamando herramienta: edit_file
✅ Coder > edit_file: File updated successfully
💬 [Respuesta del Coder]
```

### 5. Comando /search Sigue Disponible 🔍

Si quieres usar CodeSearcher explícitamente (sin modificar):

```bash
/search sistema de logging
```

Invoca directamente a CodeSearcher sin pasar por el selector.

## Casos de Uso Completos

### Caso 1: Modificar Funcionalidad Existente

**Solicitud**: "agrega manejo de errores a process_user_request"

**Flujo automático**:
1. **Selector analiza**: Detecta "agrega" + "process_user_request" (modificación)
2. **Selecciona**: CodeSearcher primero
3. **CodeSearcher**:
   - Busca process_user_request
   - Analiza código actual
   - Identifica manejo de errores existente (try/except)
   - Proporciona contexto completo
4. **Selector**: Ahora selecciona Coder
5. **Coder**:
   - Con contexto de CodeSearcher
   - Agrega manejo de errores adicional
   - Mantiene consistencia con código existente

### Caso 2: Entender Código

**Solicitud**: "cómo funciona el sistema de herramientas?"

**Flujo automático**:
1. **Selector analiza**: Detecta "cómo funciona" (análisis)
2. **Selecciona**: CodeSearcher
3. **CodeSearcher**:
   - Busca definiciones de herramientas
   - Analiza src/tools/
   - Lista todas las categorías (filesystem, git, data, web, analysis)
   - Proporciona ejemplos de uso
   - NO modifica nada

### Caso 3: Proyecto Complejo

**Solicitud**: "crea un sistema de plugins"

**Flujo automático**:
1. **Selector analiza**: Detecta "sistema" (complejo)
2. **Selecciona**: Planner
3. **Planner**:
   - Crea plan estructurado:
     - Diseñar interfaz de plugins
     - Crear sistema de carga dinámica
     - Implementar registro de plugins
     - Agregar documentación
     - Tests
4. **Planner delega**: Cada tarea al Coder
5. **Coder**: Ejecuta cada tarea del plan

### Caso 4: Tarea Simple

**Solicitud**: "git status"

**Flujo automático**:
1. **Selector analiza**: Detecta comando simple
2. **Selecciona**: Coder directamente
3. **Coder**: Ejecuta git_status()

## Testing

Ejecutar test de integración:

```bash
python test_codesearcher_integration.py
```

**Salida esperada**:
```
======================================================================
TEST: Integracion de CodeSearcher en SelectorGroupChat
======================================================================

[1] Inicializando componentes del team...
   [OK] Team creado con 3 agentes:
     1. CodeSearcher: Agente especializado en BÚSQUEDA...
     2. Planner: Planificador estratégico...
     3. Coder: Especialista en tareas simples...

[2] Verificando agentes esperados...
   [OK] CodeSearcher encontrado
   [OK] Planner encontrado
   [OK] Coder encontrado

[3] Verificando herramientas de CodeSearcher...
   [OK] CodeSearcher tiene 8 herramientas

[4] Verificando selector_prompt...
   [OK] Selector prompt configurado

======================================================================
INTEGRACION EXITOSA
======================================================================
```

## Configuración Avanzada

### Modificar criterios de selección

Edita `main.py:_setup_team()` → `selector_prompt`:

```python
selector_prompt = """
CRITERIOS DE SELECCIÓN:

1. **CodeSearcher** - Para...
   Señales clave: "dónde", "cómo", "busca", "analiza"

2. **Planner** - Para...
   Señales clave: "sistema", "aplicación", "completo"

3. **Coder** - Para...
   Señales clave: "crea", "modifica", "ejecuta"
"""
```

### Agregar más agentes

```python
# Crear nuevo agente
documentation_agent = DocumentationAgent(...)

# Agregar al team
self.team = SelectorGroupChat(
    participants=[
        self.code_searcher.searcher_agent,
        self.planner.planner_agent,
        self.coder_agent,
        documentation_agent  # Nuevo agente
    ],
    ...
)
```

### Ajustar condiciones de terminación

```python
# Más mensajes antes de terminar
termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(50)

# Solo terminar con TERMINATE explícito
termination = TextMentionTermination("TERMINATE")
```

## Troubleshooting

### El selector no elige el agente correcto

**Solución**: Ajustar el `selector_prompt` con mejores ejemplos y señales clave.

### El team no se crea correctamente

**Verificar**:
1. Los 3 agentes están inicializados (code_searcher, planner, coder)
2. El model_client es el mismo para todos
3. La termination_condition está definida

### Mensajes duplicados en streaming

**Causa**: El set `agent_messages_shown` ya maneja esto.

**Verificar**: Que se está usando el hash correcto del contenido.

## Próximos Pasos

### Mejoras Planeadas

1. **Agent de Testing**: Agente especializado en crear y ejecutar tests
2. **Agent de Documentación**: Generación automática de docs
3. **Agent de Refactoring**: Análisis y refactorización de código
4. **Memoria compartida**: Los agentes comparten contexto entre ellos
5. **Aprendizaje**: El selector mejora con el uso

---

**Fecha de integración**: 2025-11-01
**Versión**: 1.1.0
**Estado**: ✅ Completamente funcional y testeado
