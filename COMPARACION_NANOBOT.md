# Comparación: CodeAgent vs Nanobot - Sistema de Subagentes

## 📊 Resumen Ejecutivo

Ambos sistemas implementan **subagentes paralelos** con asyncio, pero con diferencias arquitectónicas importantes.

| Aspecto | Nanobot | CodeAgent (Nuestra Implementación) |
|---------|---------|-------------------------------------|
| **Arquitectura base** | Message Bus + Eventos | Event Bus + Factory Pattern |
| **Notificación de resultados** | InboundMessage a bus central | SubagentEvent pub/sub |
| **Creación de subagente** | Loop directo con LLM | Factory crea AgentOrchestrator aislado |
| **Integración** | Tool class-based | Function-based tool |
| **Estado de subagentes** | Lightweight, loop propio | Full orchestrator instance |
| **System prompt** | Dinámico por subagente | Hereda del main + modo headless |

---

## 🔍 Análisis Detallado

### 1. Arquitectura de Notificación

#### **Nanobot:**
```python
# Usa MessageBus central
async def _announce_result(...):
    msg = InboundMessage(
        channel="system",
        sender_id="subagent",
        chat_id=f"{origin['channel']}:{origin['chat_id']}",
        content=announce_content,
    )
    await self.bus.publish_inbound(msg)
```

**Características:**
- ✅ Integrado con sistema de mensajería (Telegram, Discord, CLI)
- ✅ Soporta múltiples canales de comunicación
- ✅ El resultado se "inyecta" como mensaje del sistema
- ❌ Más complejo, requiere bus de mensajes

#### **CodeAgent:**
```python
# Usa Event Bus dedicado
await self.event_bus.publish(SubagentEvent(
    subagent_id=subagent_id,
    parent_task_id=parent_task_id,
    event_type="completed",
    content={"label": label, "result": result, "status": "ok"}
))

# Parent se subscribe
self.subagent_event_bus.subscribe("completed", self._on_subagent_completed)
```

**Características:**
- ✅ Event bus dedicado solo para subagentes
- ✅ Pub/Sub pattern simple
- ✅ Múltiples subscriptores posibles
- ✅ Historia de eventos para debugging
- ✅ Más simple, no requiere infraestructura de mensajería

**Diferencia clave:** Nanobot usa un bus de mensajes global (para multi-platform), CodeAgent usa eventos locales (más simple).

---

### 2. Creación y Ejecución del Subagente

#### **Nanobot:**
```python
async def _run_subagent(self, task_id, task, label, origin):
    # Build tools directamente
    tools = ToolRegistry()
    tools.register(ReadFileTool())
    tools.register(WriteFileTool())
    # ... etc

    # Build system prompt específico
    system_prompt = self._build_subagent_prompt(task)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    # Loop directo con LLM
    max_iterations = 15
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        response = await self.provider.chat(
            messages=messages,
            tools=tools.get_definitions(),
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        if response.has_tool_calls:
            # Ejecutar tools...
        else:
            final_result = response.content
            break
```

**Características:**
- ✅ Lightweight - solo loop de chat
- ✅ System prompt personalizado por task
- ✅ Control granular del loop
- ❌ No reutiliza orchestrator existente
- ❌ Debe re-implementar lógica de agent loop

#### **CodeAgent:**
```python
async def _run_subagent(self, subagent_id, task, label, ...):
    # Crear tools filtrados
    isolated_tools = create_tool_subset(
        self.base_tools,
        exclude_names=["spawn_subagent"]
    )

    # Factory crea orchestrator completo
    orchestrator = self.orchestrator_factory(
        tools=isolated_tools,
        max_iterations=max_iterations,
        mode="subagent",  # Modo headless
    )

    # Usa método run_task del orchestrator
    result = await orchestrator.run_task(task)
```

**Características:**
- ✅ Reutiliza toda la lógica de AgentOrchestrator
- ✅ Factory pattern para aislamiento
- ✅ Consistent behavior entre main y subagent
- ✅ Menos código (delega al orchestrator)
- ❌ Más "pesado" - instancia completa de orchestrator
- ❌ Overhead de memoria mayor

**Diferencia clave:** Nanobot implementa loop propio (lightweight), CodeAgent reutiliza orchestrator completo (más pesado pero más consistente).

---

### 3. System Prompt para Subagentes

#### **Nanobot:**
```python
def _build_subagent_prompt(self, task: str) -> str:
    return f"""# Subagent

## Current Time
{now} ({tz})

You are a subagent spawned by the main agent to complete a specific task.

## Rules
1. Stay focused - complete only the assigned task, nothing else
2. Your final response will be reported back to the main agent
3. Do not initiate conversations or take on side tasks
4. Be concise but informative in your findings

## What You Can Do
- Read and write files in the workspace
- Execute shell commands
- Search the web and fetch web pages
- Complete the task thoroughly

## What You Cannot Do
- Send messages directly to users (no message tool available)
- Spawn other subagents
- Access the main agent's conversation history

## Workspace
Your workspace is at: {self.workspace}
Skills are available at: {self.workspace}/skills/ (read SKILL.md files as needed)

When you have completed the task, provide a clear summary of your findings or actions."""
```

**Características:**
- ✅ Muy específico y enfocado
- ✅ Restricciones claras
- ✅ Contexto de workspace
- ✅ Instrucciones de formato de resultado

#### **CodeAgent:**
```python
# Usa el mismo system prompt que el main agent
# Pero con modo "headless" que desactiva UI completa
orchestrator = AgentOrchestrator(..., headless=True)
orchestrator._is_subagent = True

# En run_task():
if hasattr(self, '_is_subagent') and self._is_subagent:
    return await self._run_task_simple(task)
```

**Características:**
- ✅ Hereda comportamiento del main
- ✅ Modo headless evita UI
- ✅ Más simple (no duplicación de prompts)
- ❌ No tiene instrucciones específicas de subagent

**Diferencia clave:** Nanobot tiene prompt específico para subagentes, CodeAgent hereda del main.

---

### 4. Integración con Tool System

#### **Nanobot:**
```python
class SpawnTool(Tool):
    """Tool class-based"""

    def __init__(self, manager: SubagentManager):
        self._manager = manager
        self._origin_channel = "cli"
        self._origin_chat_id = "direct"

    @property
    def name(self) -> str:
        return "spawn"

    @property
    def description(self) -> str:
        return "Spawn a subagent to handle a task..."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {"type": "string", ...},
                "label": {"type": "string", ...},
            },
            "required": ["task"],
        }

    async def execute(self, task: str, label: str | None = None, **kwargs):
        return await self._manager.spawn(...)
```

#### **CodeAgent:**
```python
# Function-based tool
async def spawn_subagent(
    task: str,
    label: str = None,
) -> str:
    """Spawn a background subagent..."""
    if _subagent_manager is None:
        return "Error: Subagent system not initialized"

    return await _subagent_manager.spawn(
        task=task,
        label=label,
        parent_task_id=_current_task_id,
        max_iterations=15,
    )

# Inicialización
spawn_module = sys.modules['src.tools.spawn_subagent']
spawn_module.set_subagent_manager(self.subagent_manager, task_id="main")
```

**Diferencia:** Nanobot usa clases (Tool base class), CodeAgent usa funciones async directas.

---

### 5. Filtrado de Tools (Prevención de Recursión)

#### **Nanobot:**
```python
# Hard-coded en _run_subagent
tools = ToolRegistry()
tools.register(ReadFileTool())
tools.register(WriteFileTool())
tools.register(EditFileTool())
tools.register(ListDirTool())
tools.register(ExecTool())
tools.register(WebSearchTool())
tools.register(WebFetchTool())
# Nota: NO se registra SpawnTool
```

**Enfoque:** Lista explícita de tools permitidos.

#### **CodeAgent:**
```python
# Filtrado dinámico
isolated_tools = create_tool_subset(
    self.base_tools,
    exclude_names=["spawn_subagent"]  # Blacklist
)
```

**Enfoque:** Whitelist/Blacklist flexible.

**Diferencia:** Nanobot usa whitelist hardcoded, CodeAgent usa blacklist dinámico.

---

### 6. Manejo de Resultados

#### **Nanobot:**
```python
# Inyecta resultado como mensaje del sistema
announce_content = f"""[Subagent '{label}' {status_text}]

Task: {task}

Result:
{result}

Summarize this naturally for the user. Keep it brief (1-2 sentences).
Do not mention technical details like "subagent" or task IDs."""

msg = InboundMessage(
    channel="system",
    sender_id="subagent",
    chat_id=f"{origin['channel']}:{origin['chat_id']}",
    content=announce_content,
)

await self.bus.publish_inbound(msg)
```

**Enfoque:**
- El resultado se "inyecta" como mensaje del usuario
- El main agent ve el resultado en su conversación
- El main agent debe "resumir naturalmente" el resultado

#### **CodeAgent:**
```python
# Publica evento y callback procesa
await self.event_bus.publish(SubagentEvent(
    subagent_id=subagent_id,
    event_type="completed",
    content={"label": label, "result": result, "status": "ok"}
))

# Callback en orchestrator
async def _on_subagent_completed(self, event) -> None:
    label = event.content.get('label', 'unknown')
    result = event.content.get('result', '')
    result_preview = result[:100] + "..." if len(result) > 100 else result
    self.cli.print_success(f"✓ Subagent '{label}' completed: {result_preview}")
```

**Enfoque:**
- Evento discreto
- Callback procesa y notifica
- CLI muestra notificación
- Resultado disponible para consulta

**Diferencia clave:** Nanobot "simula" mensaje del usuario, CodeAgent usa eventos y callbacks.

---

## 📋 Tabla Comparativa Completa

| Característica | Nanobot | CodeAgent |
|----------------|---------|-----------|
| **Spawn mechanism** | `asyncio.create_task` | `asyncio.create_task` |
| **Max iterations** | 15 | 15 |
| **Task ID format** | UUID[:8] | UUID[:8] |
| **Auto-cleanup** | `add_done_callback` | `add_done_callback` |
| **Recursion prevention** | Whitelist de tools | Blacklist de tools |
| **Notification** | InboundMessage al bus | SubagentEvent pub/sub |
| **Result injection** | Como mensaje del sistema | Como evento con callback |
| **Subagent loop** | Loop directo con LLM | Orchestrator.run_task() |
| **System prompt** | Customizado por subagent | Hereda del main |
| **Tool format** | Class-based (Tool) | Function-based (async def) |
| **Multi-platform** | ✅ (Telegram, Discord, CLI) | ❌ (Solo CLI) |
| **Event history** | ❌ | ✅ |
| **CLI commands** | ❌ | ✅ (/subagents, /subagent-status) |
| **Memory footprint** | Ligero (~20MB por subagent) | Pesado (~50MB por subagent) |
| **Code complexity** | Simple (loop directo) | Complejo (factory pattern) |
| **Consistency** | Loop custom vs main | Mismo comportamiento |

---

## 🎯 Recomendaciones para CodeAgent

### Mejoras inspiradas en Nanobot:

1. **✅ System Prompt Específico para Subagentes**

   Agregar en `_create_subagent_orchestrator`:
   ```python
   subagent_prompt = f"""You are a subagent spawned to complete a specific task.

   ## Rules
   1. Stay focused - complete only the assigned task
   2. Be concise but thorough
   3. Your result will be reported back to the main agent

   ## What You Cannot Do
   - Spawn other subagents
   - Access the main agent's conversation history

   When done, provide a clear summary of your findings."""

   # Inject en agent system prompt
   ```

2. **✅ Mejora en Anuncio de Resultados**

   Actualmente solo imprimimos el resultado. Nanobot lo "inyecta" como mensaje:
   ```python
   async def _on_subagent_completed(self, event) -> None:
       # En lugar de solo print_success
       # Opcionalmente inyectar como mensaje al agente:
       result_message = f"""[Background task '{label}' completed]

       Result: {result}

       Continue with your original task."""

       # Agregar a conversación del main agent
   ```

3. **Agregar Contexto de Workspace**

   Como en nanobot:
   ```python
   workspace_path = Path.cwd()
   subagent_prompt += f"\n\nWorkspace: {workspace_path}"
   ```

4. **Logging Mejorado**

   Nanobot usa loguru con structured logging:
   ```python
   logger.info(f"Subagent [{task_id}] starting task: {label}")
   logger.debug(f"Subagent [{task_id}] executing: {tool_name} with args: {args}")
   ```

---

## 🚀 Conclusión

### **Nanobot:**
- ✅ Lightweight y eficiente
- ✅ Multi-platform (Telegram, Discord, CLI)
- ✅ System prompt específico para subagentes
- ✅ Resultado se inyecta naturalmente en conversación
- ❌ Loop custom (no reusa código del main)
- ❌ No tiene CLI commands de inspección

### **CodeAgent:**
- ✅ Reutiliza orchestrator completo (consistent behavior)
- ✅ Event bus dedicado con historia
- ✅ CLI commands para monitoreo (/subagents, /subagent-status)
- ✅ Factory pattern bien diseñado
- ❌ Más pesado (memory footprint)
- ❌ No tiene system prompt específico para subagents
- ❌ Resultado solo se muestra, no se integra en conversación

---

## 💡 Comportamiento Actual vs Nanobot

**Pregunta:** ¿Cómo funciona actualmente CodeAgent vs Nanobot?

### **CodeAgent (Actual):**
```
Usuario: "Analiza file1 y file2 en paralelo"
Agente: [Spawns 2 subagents]
        → Subagent 'analyzer-1' spawned (ID: abc123)
        → Subagent 'analyzer-2' spawned (ID: def456)

[Subagents ejecutan en background]

[CLI muestra notificación:]
✓ Subagent 'analyzer-1' completed: Found 100 lines...
✓ Subagent 'analyzer-2' completed: Found 200 lines...

[Agente puede acceder a resultados pero NO se inyectan automáticamente]
```

### **Nanobot:**
```
Usuario: "Analiza file1 y file2 en paralelo"
Agente: [Spawns 2 subagents]
        → Subagent [task1] started (id: abc123)
        → Subagent [task2] started (id: def456)

[Subagents ejecutan]

[MessageBus inyecta resultado como mensaje del sistema:]
[Sistema] Subagent 'task1' completed successfully

Task: Analyze file1

Result: File has 100 lines, 10 functions...

Summarize this naturally for the user.

[Agente ve el mensaje y responde:]
"File1 has been analyzed and has 100 lines with 10 functions.
File2 analysis shows..."
```

**Diferencia clave:** Nanobot "simula" que el resultado es un mensaje, CodeAgent usa notificaciones discretas.

---

¿Quieres que implemente alguna de estas mejoras inspiradas en nanobot? Las más importantes serían:

1. ✅ System prompt específico para subagents
2. ✅ Inyección de resultados en conversación del main
3. ✅ Logging estructurado mejorado
