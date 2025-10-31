# Code Agent CLI - Interfaz Interactiva

Agente inteligente de desarrollo con planificación dinámica de tareas y gestión automática de historial de conversaciones.

## Características

✨ **Planificación Inteligente**: Crea automáticamente un plan de ejecución con tareas específicas
🔄 **Re-planificación Dinámica**: Adapta el plan si encuentra errores o nueva información
💾 **Gestión de Historial**: Compresión automática cuando el historial crece
🎨 **Interfaz Rica**: CLI interactiva con colores y formato enriquecido
🛠️ **Herramientas Integradas**: Lectura/escritura de archivos, búsqueda, ejecución de comandos

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Iniciar el agente

```bash
python main.py
```

### Comandos disponibles

- `/help` - Muestra la ayuda
- `/new` - Inicia una nueva conversación sin historial (limpia todo el contexto)
- `/clear` - Limpia el historial de conversación
- `/plan` - Muestra el plan de ejecución actual
- `/stats` - Muestra estadísticas de la sesión
- `/save <archivo>` - Guarda el historial en un archivo
- `/load <archivo>` - Carga un historial desde un archivo
- `/exit` o `/quit` - Salir del agente

### Ejemplos de uso

**Ejemplo 1: Crear una API**
```
Tu: Crea una API REST con FastAPI que tenga endpoints para gestionar usuarios (CRUD completo)
```

El agente:
1. Creará un plan con tareas como:
   - Verificar si existe FastAPI en el proyecto
   - Crear estructura de directorios
   - Crear modelos de datos
   - Implementar endpoints CRUD
   - Crear archivo main.py
   - Agregar documentación

2. Te mostrará el plan y pedirá confirmación

3. Ejecutará cada tarea secuencialmente

4. Si encuentra errores, re-planificará automáticamente


**Ejemplo 2: Refactorizar código**
```
Tu: Encuentra todos los archivos Python que usan callbacks y refactorízalos para usar async/await
```

**Ejemplo 3: Corrección de bugs**
```
Tu: Busca y corrige todos los errores de tipo en el proyecto
```

### Ejemplo 4: Iniciar nueva conversación

```
Tu: /new

[El agente limpia todo el historial y el plan actual]
[Puedes comenzar con una tarea completamente nueva sin contexto previo]

Tu: Ahora ayúdame a crear un sistema de autenticación con JWT
```

El comando `/new` es útil cuando:

- Quieres cambiar completamente de tarea
- El historial se ha vuelto muy largo y prefieres empezar de cero
- Necesitas que el agente "olvide" el contexto anterior
- Quieres asegurarte de que no hay interferencia de tareas previas

## Arquitectura

### Componentes Principales

#### 1. ConversationManager (`conversation_manager.py`)
Gestiona el historial de conversaciones con compresión automática:
- Estima tokens usados
- Crea resúmenes cuando el historial crece
- Mantiene contexto relevante para el agente

#### 2. TaskPlanner (`task_planner.py`)
Sistema de planificación con dos agentes especializados:
- **Planner Agent**: Crea planes de ejecución estructurados
- **PlanUpdater Agent**: Adapta planes basándose en resultados
- Gestiona dependencias entre tareas
- Actualiza estados (pending, in_progress, completed, failed, blocked)

#### 3. TaskExecutor (`task_executor.py`)
Ejecutor con re-planificación dinámica:
- Ejecuta tareas del plan secuencialmente
- Detecta cuando necesita re-planificar
- Comprime historial automáticamente
- Maneja errores y reintentos

#### 4. CLIInterface (`cli_interface.py`)
Interfaz CLI rica e interactiva:
- Usa `rich` para formato enriquecido
- Usa `prompt-toolkit` para autocompletado
- Muestra progreso en tiempo real
- Formatos visuales para planes y resultados

### Flujo de Trabajo

```
Usuario ingresa solicitud
         ↓
ConversationManager guarda en historial
         ↓
TaskPlanner crea plan de ejecución
         ↓
CLI muestra plan y pide confirmación
         ↓
TaskExecutor ejecuta tareas
         ↓
Por cada tarea:
    ├─ Ejecuta usando CoderAgent
    ├─ Analiza resultado
    ├─ ¿Necesita re-planificar? → TaskPlanner actualiza plan
    └─ Continúa con siguiente tarea
         ↓
¿Historial muy grande? → ConversationManager comprime
         ↓
Plan completado → Muestra resumen
```

## Estructura de Archivos

```
CodeAgent/
├── main.py                      # Punto de entrada principal
├── conversation_manager.py       # Gestión de historial
├── task_planner.py              # Planificación de tareas
├── task_executor.py             # Ejecución de tareas
├── cli_interface.py             # Interfaz CLI
├── coder.py                     # Agente de código original
├── tools.py                     # Herramientas del agente
├── prompt.py                    # Prompts del sistema
├── requirements.txt             # Dependencias
└── README_CLI.md               # Esta documentación
```

## Configuración

### Cambiar el modelo

Edita `main.py`:

```python
self.model_client = OpenAIChatCompletionClient(
    model="tu-modelo",           # Cambiar aquí
    base_url="tu-base-url",      # Cambiar aquí
    api_key="tu-api-key",        # Cambiar aquí
    model_capabilities={
        "vision": True,
        "function_calling": True,
        "json_output": True,
    },
)
```

### Ajustar límites de historial

Edita `main.py`:

```python
self.conversation_manager = ConversationManager(
    max_tokens=8000,              # Límite máximo
    summary_threshold=6000        # Umbral para comprimir
)
```

## Características Avanzadas

### Planificación con Dependencias

El sistema maneja automáticamente dependencias entre tareas:

```python
Task(
    id=2,
    title="Crear modelos",
    dependencies=[1]  # Depende de tarea 1
)
```

### Re-planificación Inteligente

El sistema detecta automáticamente cuándo re-planificar basándose en:
- Errores en la ejecución
- Resultados inesperados
- Palabras clave en los resultados ("error", "falta", "necesario", etc.)

### Compresión de Historial

Cuando el historial excede el umbral:
1. Crea un prompt de resumen
2. Usa un agente Summarizer para generar resumen conciso
3. Mantiene solo los últimos 3 mensajes + resumen
4. Reduce uso de tokens significativamente

## Solución de Problemas

### Error: "No se pudo generar el plan"
- Verifica que el modelo soporte JSON estructurado
- Revisa la API key y conectividad

### Error: "Límite de iteraciones alcanzado"
- El plan tiene dependencias circulares
- Aumenta `max_iterations` en `task_executor.py`

### El agente no responde
- Verifica que todas las dependencias estén instaladas
- Revisa los logs de error en la consola

## Contribuir

Para agregar nuevas herramientas al agente:

1. Crea la función en `tools.py`
2. Agrégala a `coder_tools` en `main.py`
3. El agente la detectará automáticamente

## Licencia

Este proyecto es de código abierto.
