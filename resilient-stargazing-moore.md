# Plan de Implementación: Sistema de Ejecución Paralela de Subagentes

## Resumen Ejecutivo

Implementar sistema de **ejecución paralela de subagentes** inspirado en nanobot dentro de CodeAgent, preservando la arquitectura AutoGen existente.

### Prioridades (según feedback del usuario)
1. **ALTA**: ✅ Ejecución paralela de subagentes (spawn tool)
2. **MEDIA**: Sistema de jobs con cola y prioridades (opcional, para Phase 2)
3. **BAJA**: Cron/Scheduler (futuro)
4. **BAJA**: Message Bus completo (solo lo necesario para subagents)

### Decisiones Arquitectónicas
- ✅ **Migración gradual**: Wrapper para tools existentes, sin reescritura
- ✅ **Estado aislado**: Cada subagent tiene su propia copia de estado
- ✅ **Integración mínima**: JobOrchestrator envuelve SelectorGroupChat sin modificarlo

---

## Arquitectura Propuesta

### Componentes Principales

```
CodeAgent (Actual)                  CodeAgent + Jobs (Nuevo)
─────────────────                   ─────────────────────────

┌─────────────────┐                 ┌──────────────────────────┐
│ SelectorGroup   │                 │   JobOrchestrator        │
│ Chat (AutoGen)  │──────────────>  │  - Job Queue             │
│ - Planner       │                 │  - Priority Scheduler    │
│ - Coder         │                 │  - Worker Pool           │
└─────────────────┘                 └──────────────────────────┘
                                              │
        │                                     ├─────────────┐
        │                                     ▼             ▼
        ▼                           ┌─────────────┐  ┌──────────┐
┌─────────────┐                     │ SubAgent    │  │ SubAgent │
│ Tools       │                     │ Manager     │  │ Manager  │
│ (40+ tools) │                     └─────────────┘  └──────────┘
└─────────────┘                              │             │
                                             ▼             ▼
        │                           ┌──────────────────────────┐
        │                           │   Message Bus (async)    │
        │                           │  - Inbound Queue         │
        │                           │  - Outbound Queue        │
        │                           │  - Event Subscribers     │
        ▼                           └──────────────────────────┘
┌─────────────┐                              │
│ Sequential  │                              ├──────────────┐
│ Execution   │                              ▼              ▼
└─────────────┘                     ┌──────────────┐  ┌─────────────┐
                                    │ Cron Service │  │ Tool        │
                                    │ - at/every   │  │ Registry    │
                                    │ - cron expr  │  │ (dynamic)   │
                                    └──────────────┘  └─────────────┘
```

---

## Fase 1: Infraestructura Mínima para Subagents

### 1.1 Event Bus Simplificado (solo para subagents)

**Archivo**: `src/subagents/events.py`

```python
from dataclasses import dataclass
from typing import Any, Callable
import asyncio
from datetime import datetime

@dataclass
class SubagentEvent:
    """Eventos de ciclo de vida de subagents"""
    subagent_id: str
    parent_task_id: str
    event_type: str  # "spawned", "progress", "completed", "failed"
    content: Any
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()

class SubagentEventBus:
    """Event bus minimalista solo para comunicación parent-subagent"""
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._event_history: list[SubagentEvent] = []

    async def publish(self, event: SubagentEvent):
        """Publish event and notify subscribers"""
        self._event_history.append(event)

        # Notify subscribers
        for callback in self._subscribers.get(event.event_type, []):
            try:
                await callback(event)
            except Exception as e:
                print(f"Error in event subscriber: {e}")

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to specific event type"""
        self._subscribers.setdefault(event_type, []).append(callback)

    def get_events_for_subagent(self, subagent_id: str) -> list[SubagentEvent]:
        """Get all events for a specific subagent"""
        return [e for e in self._event_history if e.subagent_id == subagent_id]
```

---

## Fase 2: Tool Wrapper Simplificado (sin refactorización)

### 2.1 Función Wrapper para Tools Existentes

**Archivo**: `src/subagents/tool_wrapper.py`

```python
from typing import Callable, Any

def create_tool_subset(
    all_tools: list[Callable],
    exclude_names: list[str] = None
) -> list[Callable]:
    """
    Crea un subset de tools excluyendo los especificados.
    NO requiere refactorizar tools existentes.

    Args:
        all_tools: Lista de funciones async que son tools
        exclude_names: Nombres de tools a excluir (e.g., ["spawn_subagent"])

    Returns:
        Lista filtrada de tools
    """
    exclude_names = exclude_names or []

    filtered_tools = []
    for tool in all_tools:
        tool_name = tool.__name__
        if tool_name not in exclude_names:
            filtered_tools.append(tool)

    return filtered_tools

def get_tool_names(tools: list[Callable]) -> list[str]:
    """Get names of all tools in a list"""
    return [tool.__name__ for tool in tools]
```

**VENTAJA**: No necesitamos crear clases BaseTool ni ToolRegistry. Simplemente filtramos la lista de funciones existentes.

---

## Fase 3: SubAgent Manager (CORE del sistema)

### 3.1 SubAgent Manager (versión simplificada con integración mínima)

**Archivo**: `src/subagents/manager.py`

```python
import asyncio
import uuid
from typing import Callable, Any
from datetime import datetime
from .events import SubagentEventBus, SubagentEvent
from .tool_wrapper import create_tool_subset

class SubAgentManager:
    """
    Gestiona ejecución paralela de subagents.
    Integración MÍNIMA: usa AgentOrchestrator existente sin modificarlo.
    """

    def __init__(
        self,
        event_bus: SubagentEventBus,
        orchestrator_factory: Callable,  # Factory: crea AgentOrchestrator con config específica
        base_tools: list[Callable],  # Tools disponibles para subagents
    ):
        self.event_bus = event_bus
        self.orchestrator_factory = orchestrator_factory
        self.base_tools = base_tools
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._results: dict[str, dict] = {}  # Cache de resultados

    async def spawn(
        self,
        task: str,
        label: str = None,
        parent_task_id: str = "main",
        max_iterations: int = 15,
    ) -> str:
        """
        Spawn a background subagent to run task in parallel.

        Args:
            task: Task description for the subagent
            label: Human-readable label for the subagent
            parent_task_id: ID of parent task (for event routing)
            max_iterations: Max iterations for subagent

        Returns:
            Subagent ID
        """
        subagent_id = str(uuid.uuid4())[:8]
        label = label or "background task"

        # Create background asyncio task
        bg_task = asyncio.create_task(
            self._run_subagent(
                subagent_id=subagent_id,
                task=task,
                label=label,
                parent_task_id=parent_task_id,
                max_iterations=max_iterations,
            )
        )

        self._running_tasks[subagent_id] = bg_task

        # Auto-cleanup when done
        bg_task.add_done_callback(
            lambda _: self._running_tasks.pop(subagent_id, None)
        )

        # Publish spawn event
        await self.event_bus.publish(SubagentEvent(
            subagent_id=subagent_id,
            parent_task_id=parent_task_id,
            event_type="spawned",
            content={"task": task, "label": label}
        ))

        return f"Subagent '{label}' spawned (ID: {subagent_id})"

    async def _run_subagent(
        self,
        subagent_id: str,
        task: str,
        label: str,
        parent_task_id: str,
        max_iterations: int,
    ):
        """Execute subagent in isolated context"""
        try:
            # Create isolated tools (exclude recursive tools)
            isolated_tools = create_tool_subset(
                self.base_tools,
                exclude_names=["spawn_subagent"]  # Prevent infinite recursion
            )

            # Create isolated orchestrator instance
            # CLAVE: Usa factory pattern, NO modifica AgentOrchestrator existente
            orchestrator = self.orchestrator_factory(
                tools=isolated_tools,
                max_iterations=max_iterations,
                mode="subagent",  # Indica que es subagent (no UI completa)
            )

            # Run the task using existing AgentOrchestrator logic
            result = await orchestrator.run_task(task)

            # Store result
            self._results[subagent_id] = {
                "status": "ok",
                "result": result,
                "label": label,
            }

            # Publish completion event
            await self.event_bus.publish(SubagentEvent(
                subagent_id=subagent_id,
                parent_task_id=parent_task_id,
                event_type="completed",
                content={
                    "label": label,
                    "result": result,
                    "status": "ok"
                }
            ))

        except Exception as e:
            # Store error
            self._results[subagent_id] = {
                "status": "error",
                "error": str(e),
                "label": label,
            }

            # Publish failure event
            await self.event_bus.publish(SubagentEvent(
                subagent_id=subagent_id,
                parent_task_id=parent_task_id,
                event_type="failed",
                content={
                    "label": label,
                    "error": str(e),
                    "status": "error"
                }
            ))

    async def get_status(self, subagent_id: str) -> dict:
        """Get current status of a subagent"""
        task = self._running_tasks.get(subagent_id)

        if task is None:
            # Check if we have cached result
            if subagent_id in self._results:
                return {
                    "status": "completed",
                    **self._results[subagent_id]
                }
            return {"status": "not_found"}

        if task.done():
            return {
                "status": "completed",
                **self._results.get(subagent_id, {})
            }

        return {
            "status": "running",
            "done": False,
        }

    def list_active_subagents(self) -> list[dict]:
        """List all currently running subagents"""
        return [
            {
                "id": subagent_id,
                "status": "running",
            }
            for subagent_id, task in self._running_tasks.items()
            if not task.done()
        ]
```

**DISEÑO CLAVE**:
- ✅ No modifica `AgentOrchestrator` internamente
- ✅ Usa factory pattern para crear instancias aisladas
- ✅ Estado aislado: cada subagent tiene su propia instancia de orchestrator
- ✅ Event-driven: comunica progreso via events

### 3.2 Spawn Tool (función async simple)

**Archivo**: `src/tools/spawn_subagent.py`

```python
"""
Spawn subagent tool - permite al agente principal crear subagents en paralelo.
Compatible con sistema de tools existente (función async, no clase).
"""

from ..subagents.manager import SubAgentManager

# Global reference (será inyectada por orchestrator)
_subagent_manager: SubAgentManager = None
_current_task_id: str = "main"

def set_subagent_manager(manager: SubAgentManager, task_id: str = "main"):
    """Initialize the spawn tool with manager instance"""
    global _subagent_manager, _current_task_id
    _subagent_manager = manager
    _current_task_id = task_id

async def spawn_subagent(
    task: str,
    label: str = None,
) -> str:
    """
    Spawn a background subagent to handle a task in parallel.

    The subagent will:
    - Run independently with isolated tools (no recursive spawning)
    - Execute up to 15 iterations
    - Report results when completed via events

    Use this for tasks that can be done concurrently, such as:
    - Analyzing different files in parallel
    - Running tests while writing documentation
    - Researching multiple topics simultaneously

    Args:
        task: Detailed description of what the subagent should do
        label: Short human-readable label (e.g., "test runner", "docs writer")

    Returns:
        Confirmation message with subagent ID

    Example:
        result = await spawn_subagent(
            task="Run all tests in the tests/ directory and report failures",
            label="test runner"
        )
    """
    if _subagent_manager is None:
        return "Error: Subagent system not initialized"

    return await _subagent_manager.spawn(
        task=task,
        label=label,
        parent_task_id=_current_task_id,
        max_iterations=15,
    )

# Tool metadata for AutoGen (será leído por orchestrator.py)
spawn_subagent._tool_name = "spawn_subagent"
spawn_subagent._tool_description = """Spawn a background subagent to handle a task in parallel.
The subagent runs independently and reports results when done.
Use for concurrent tasks like parallel file analysis or simultaneous testing."""
```

**VENTAJA**: Compatible con el sistema actual que usa funciones async directamente.

---

## Fase 4: Integración con AgentOrchestrator (MÍNIMA)

### 4.1 Factory Pattern para Subagents

**Modificación en**: `src/config/orchestrator.py`

```python
class AgentOrchestrator:
    def __init__(self, ...):
        # ... código existente ...

        # NEW: SubAgent system initialization
        from ..subagents.events import SubagentEventBus
        from ..subagents.manager import SubAgentManager
        from ..tools import spawn_subagent

        self.subagent_event_bus = SubagentEventBus()
        self.subagent_manager = SubAgentManager(
            event_bus=self.subagent_event_bus,
            orchestrator_factory=self._create_subagent_orchestrator,
            base_tools=self.read_only + self.modification,  # Todos los tools existentes
        )

        # Initialize spawn tool
        spawn_subagent.set_subagent_manager(self.subagent_manager, task_id="main")

        # Add spawn tool to coder agent
        self.coder_agent.tools.append(spawn_subagent)

        # Subscribe to subagent completion events
        self.subagent_event_bus.subscribe("completed", self._on_subagent_completed)
        self.subagent_event_bus.subscribe("failed", self._on_subagent_failed)

    def _create_subagent_orchestrator(
        self,
        tools: list[Callable],
        max_iterations: int,
        mode: str = "subagent"
    ) -> 'AgentOrchestrator':
        """
        Factory method to create isolated AgentOrchestrator for subagents.
        CLAVE: Reutiliza la clase existente sin modificarla.
        """
        # Create new instance with isolated config
        subagent = AgentOrchestrator(
            model_name_base=self.model_name_base,
            model_name_strong=self.model_name_strong,
            api_endpoint=self.api_endpoint,
            api_key=self.api_key,
            mode=mode,  # "subagent" mode = no UI, simplified logging
        )

        # Override tools with isolated subset
        subagent.coder_agent._tools = tools
        subagent.coder_agent.max_tool_iterations = max_iterations

        # Disable subagent spawning for this instance (prevent recursion)
        # (ya filtrado en create_tool_subset, pero doble verificación)

        return subagent

    async def run_task(self, task: str) -> str:
        """
        Run a task using the agent team.
        Usado tanto por main task como por subagents.
        """
        # Usar lógica existente de process_user_request
        # pero sin UI completa si mode="subagent"

        if hasattr(self, 'mode') and self.mode == "subagent":
            # Simplified execution for subagents
            result = await self._run_task_simple(task)
        else:
            # Full UI execution for main task
            result = await self.process_user_request(task)

        return result

    async def _run_task_simple(self, task: str) -> str:
        """Simplified task execution for subagents (no full UI)"""
        # Create task context
        task_context = TaskContext(query=task)

        # Run through main_team
        stream = self.main_team.run_stream(task=task_context)

        # Collect result
        result_parts = []
        async for msg in stream:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                result_parts.append(msg.content)

        return "\n".join(result_parts)

    async def _on_subagent_completed(self, event: SubagentEvent):
        """Handle subagent completion"""
        # Log to console
        self.cli.print_info(
            f"✓ Subagent {event.content['label']} completed: {event.content['result'][:100]}..."
        )

        # Optionally inject result into main conversation
        # (para que el agente principal sepa que el subagent terminó)

    async def _on_subagent_failed(self, event: SubagentEvent):
        """Handle subagent failure"""
        self.cli.print_error(
            f"✗ Subagent {event.content['label']} failed: {event.content['error']}"
        )
```

**DISEÑO**:
- ✅ Usa `AgentOrchestrator` existente sin cambios internos
- ✅ Factory pattern crea instancias aisladas para subagents
- ✅ Modo "subagent" para ejecución simplificada (no full UI)
- ✅ Event subscribers para notificar al parent cuando subagent termina

---

## ~~Fase 5: Cron System~~ (POSPUESTA - no prioritaria)

_Esta fase se implementará en el futuro si se necesita scheduling._

---

## Fase 5: CLI Commands para Subagents

### 4.1 Job Queue

**Archivo**: `src/jobs/queue.py`

```python
import asyncio
from typing import Optional
from .types import Job, JobPriority, JobStatus
import heapq

class JobQueue:
    def __init__(self):
        self._queue: list[tuple[int, float, Job]] = []  # (priority, timestamp, job)
        self._jobs_by_id: dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def submit(self, job: Job) -> str:
        async with self._lock:
            self._jobs_by_id[job.id] = job
            # Heap with negative priority for max-heap behavior
            heapq.heappush(self._queue, (-job.priority.value, job.created_at, job))
            return job.id

    async def get_next(self) -> Optional[Job]:
        async with self._lock:
            while self._queue:
                _, _, job = heapq.heappop(self._queue)
                if job.status == JobStatus.PENDING:
                    return job
            return None

    async def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs_by_id.get(job_id)

    async def update_status(self, job_id: str, status: JobStatus, result: str = None, error: str = None):
        job = self._jobs_by_id.get(job_id)
        if job:
            job.status = status
            if result:
                job.result = result
            if error:
                job.error = error
```

### 4.2 Job Orchestrator

**Archivo**: `src/jobs/orchestrator.py`

```python
import asyncio
from typing import Callable
from .queue import JobQueue
from .types import Job, JobStatus, JobPriority
from ..bus.queue import MessageBus, JobMessage
from datetime import datetime

class JobOrchestrator:
    def __init__(
        self,
        message_bus: MessageBus,
        max_concurrent_jobs: int = 3,
        agent_executor: Callable = None,  # Function to execute a job with an agent
    ):
        self.bus = message_bus
        self.queue = JobQueue()
        self.max_concurrent = max_concurrent_jobs
        self.agent_executor = agent_executor
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []

    async def submit_job(self, task: str, priority: JobPriority = JobPriority.NORMAL, context: dict = None) -> str:
        job = Job(task=task, priority=priority, context=context or {})
        job_id = await self.queue.submit(job)

        await self.bus.publish(JobMessage(
            job_id=job_id,
            type="job_submitted",
            content={"task": task, "priority": priority.name},
            timestamp=datetime.now().timestamp(),
            metadata={}
        ))

        return job_id

    async def start(self):
        """Start worker pool"""
        self._running = True
        self._worker_tasks = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_concurrent)
        ]

    async def stop(self):
        """Stop worker pool"""
        self._running = False
        for task in self._worker_tasks:
            task.cancel()
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

    async def _worker(self, worker_id: int):
        """Worker that processes jobs from queue"""
        while self._running:
            try:
                job = await self.queue.get_next()
                if not job:
                    await asyncio.sleep(0.5)
                    continue

                # Mark as running
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now().timestamp()
                job.assigned_agent = f"worker_{worker_id}"

                await self.bus.publish(JobMessage(
                    job_id=job.id,
                    type="job_started",
                    content={"worker_id": worker_id, "task": job.task},
                    timestamp=datetime.now().timestamp(),
                    metadata={}
                ))

                # Execute job
                try:
                    result = await self.agent_executor(job)
                    await self.queue.update_status(job.id, JobStatus.COMPLETED, result=result)
                    job.completed_at = datetime.now().timestamp()

                    await self.bus.publish(JobMessage(
                        job_id=job.id,
                        type="job_completed",
                        content={"result": result},
                        timestamp=datetime.now().timestamp(),
                        metadata={}
                    ))

                except Exception as e:
                    await self.queue.update_status(job.id, JobStatus.FAILED, error=str(e))
                    job.completed_at = datetime.now().timestamp()

                    await self.bus.publish(JobMessage(
                        job_id=job.id,
                        type="job_failed",
                        content={"error": str(e)},
                        timestamp=datetime.now().timestamp(),
                        metadata={}
                    ))

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
```

---

## Fase 5: Cron System

### 5.1 Tipos de Cron

**Archivo**: `src/cron/types.py`

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class CronSchedule:
    kind: Literal["at", "every", "cron"]
    at_ms: int | None = None        # Unix timestamp in ms for "at"
    every_ms: int | None = None      # Interval in ms for "every"
    expr: str | None = None          # Cron expression for "cron"
    tz: str | None = None           # Timezone

@dataclass
class CronJobState:
    next_run_at_ms: int | None
    last_run_at_ms: int | None
    run_count: int = 0
    status: str = "idle"

@dataclass
class CronJob:
    id: str
    name: str
    enabled: bool
    schedule: CronSchedule
    task: str  # Task description to execute
    priority: str = "NORMAL"
    state: CronJobState = None
    created_at_ms: int = 0
    delete_after_run: bool = False
```

### 5.2 Cron Service

**Archivo**: `src/cron/service.py`

```python
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Callable
from .types import CronJob, CronSchedule, CronJobState
from ..jobs.types import JobPriority

class CronService:
    def __init__(
        self,
        storage_path: Path,
        on_job_trigger: Callable[[CronJob], asyncio.Task],  # Callback to submit job
    ):
        self.storage = storage_path
        self.on_job_trigger = on_job_trigger
        self._jobs: list[CronJob] = []
        self._timer_task: asyncio.Task | None = None
        self._load_jobs()

    def add_job(self, name: str, schedule: CronSchedule, task: str, priority: str = "NORMAL") -> str:
        """Add a new cron job"""
        import uuid
        job_id = str(uuid.uuid4())[:8]

        now_ms = int(datetime.now().timestamp() * 1000)
        next_run = self._compute_next_run(schedule, now_ms)

        job = CronJob(
            id=job_id,
            name=name,
            enabled=True,
            schedule=schedule,
            task=task,
            priority=priority,
            state=CronJobState(next_run_at_ms=next_run, last_run_at_ms=None),
            created_at_ms=now_ms,
            delete_after_run=(schedule.kind == "at"),
        )

        self._jobs.append(job)
        self._save_jobs()
        self._arm_timer()

        return job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a cron job"""
        before = len(self._jobs)
        self._jobs = [j for j in self._jobs if j.id != job_id]
        if len(self._jobs) < before:
            self._save_jobs()
            self._arm_timer()
            return True
        return False

    def list_jobs(self) -> list[dict]:
        """List all jobs"""
        return [
            {
                "id": j.id,
                "name": j.name,
                "enabled": j.enabled,
                "schedule": j.schedule,
                "task": j.task,
                "next_run": datetime.fromtimestamp(j.state.next_run_at_ms / 1000) if j.state.next_run_at_ms else None,
            }
            for j in self._jobs
        ]

    def _compute_next_run(self, schedule: CronSchedule, now_ms: int) -> int | None:
        """Compute next run time"""
        if schedule.kind == "at":
            return schedule.at_ms if schedule.at_ms > now_ms else None

        if schedule.kind == "every":
            return now_ms + schedule.every_ms

        if schedule.kind == "cron":
            from croniter import croniter
            base_dt = datetime.fromtimestamp(now_ms / 1000)
            cron = croniter(schedule.expr, base_dt)
            next_dt = cron.get_next(datetime)
            return int(next_dt.timestamp() * 1000)

        return None

    def _arm_timer(self):
        """Set timer for next job"""
        if self._timer_task:
            self._timer_task.cancel()

        enabled_jobs = [j for j in self._jobs if j.enabled and j.state.next_run_at_ms]
        if not enabled_jobs:
            return

        next_job = min(enabled_jobs, key=lambda j: j.state.next_run_at_ms)
        now_ms = int(datetime.now().timestamp() * 1000)
        delay_s = max(0, (next_job.state.next_run_at_ms - now_ms) / 1000)

        async def timer_tick():
            await asyncio.sleep(delay_s)
            await self._on_timer()

        self._timer_task = asyncio.create_task(timer_tick())

    async def _on_timer(self):
        """Execute due jobs"""
        now_ms = int(datetime.now().timestamp() * 1000)

        due_jobs = [
            j for j in self._jobs
            if j.enabled and j.state.next_run_at_ms and now_ms >= j.state.next_run_at_ms
        ]

        for job in due_jobs:
            await self._execute_job(job)

        self._arm_timer()

    async def _execute_job(self, job: CronJob):
        """Execute a cron job by submitting to job orchestrator"""
        now_ms = int(datetime.now().timestamp() * 1000)

        # Trigger callback
        await self.on_job_trigger(job)

        # Update state
        job.state.last_run_at_ms = now_ms
        job.state.run_count += 1

        # Handle one-time jobs
        if job.schedule.kind == "at":
            if job.delete_after_run:
                self._jobs.remove(job)
            else:
                job.enabled = False
        else:
            # Compute next run
            job.state.next_run_at_ms = self._compute_next_run(job.schedule, now_ms)

        self._save_jobs()

    def _load_jobs(self):
        """Load jobs from storage"""
        if self.storage.exists():
            data = json.loads(self.storage.read_text())
            # Parse JSON to CronJob objects
            # ... (implementation)

    def _save_jobs(self):
        """Save jobs to storage"""
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        # Serialize to JSON
        # ... (implementation)
```

### 5.3 Cron Tool

**Archivo**: `src/tools/cron_tool.py`

```python
from .base import BaseTool
from ..cron.service import CronService
from ..cron.types import CronSchedule

class CronTool(BaseTool):
    def __init__(self, cron_service: CronService):
        self.service = cron_service

    @property
    def name(self) -> str:
        return "cron"

    @property
    def description(self) -> str:
        return """Manage scheduled tasks (cron jobs).
        Actions: add, list, remove
        Schedule types: at (one-time), every (interval), cron (cron expression)"""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "list", "remove"]},
                "name": {"type": "string"},
                "schedule_type": {"type": "string", "enum": ["at", "every", "cron"]},
                "schedule_value": {"type": "string"},
                "task": {"type": "string"},
                "priority": {"type": "string", "enum": ["LOW", "NORMAL", "HIGH", "CRITICAL"]},
                "job_id": {"type": "string"},
            },
            "required": ["action"]
        }

    async def execute(
        self,
        action: str,
        name: str = None,
        schedule_type: str = None,
        schedule_value: str = None,
        task: str = None,
        priority: str = "NORMAL",
        job_id: str = None,
    ) -> str:
        if action == "add":
            schedule = self._parse_schedule(schedule_type, schedule_value)
            job_id = self.service.add_job(name, schedule, task, priority)
            return f"Cron job '{name}' added with ID: {job_id}"

        elif action == "list":
            jobs = self.service.list_jobs()
            return "\n".join([f"{j['id']}: {j['name']} - {j['schedule']}" for j in jobs])

        elif action == "remove":
            success = self.service.remove_job(job_id)
            return f"Job {job_id} removed" if success else f"Job {job_id} not found"

        return "Invalid action"

    def _parse_schedule(self, schedule_type: str, value: str) -> CronSchedule:
        # Parse schedule based on type
        # ... (implementation)
        pass
```

---

## Fase 6: Integración con AgentOrchestrator

### 6.1 Modificar AgentOrchestrator

**Archivo**: `src/config/orchestrator.py` (modificaciones)

```python
class AgentOrchestrator:
    def __init__(self, ...):
        # ... existing code ...

        # NEW: Initialize job system
        self.message_bus = MessageBus()
        self.tool_registry = ToolRegistry()
        self.subagent_manager = SubAgentManager(
            message_bus=self.message_bus,
            tool_registry=self.tool_registry,
            orchestrator_factory=self._create_isolated_orchestrator,
        )

        # NEW: Job orchestrator
        self.job_orchestrator = JobOrchestrator(
            message_bus=self.message_bus,
            max_concurrent_jobs=3,
            agent_executor=self._execute_job_with_agent,
        )

        # NEW: Cron service
        cron_storage = Path(".daveagent/cron/jobs.json")
        self.cron_service = CronService(
            storage_path=cron_storage,
            on_job_trigger=self._on_cron_trigger,
        )

        # NEW: Migrate existing tools to registry
        self._migrate_tools_to_registry()

        # NEW: Add spawn and cron tools
        self.tool_registry.register(SpawnSubagentTool(self.subagent_manager, current_job_id="main"))
        self.tool_registry.register(CronTool(self.cron_service))

    def _migrate_tools_to_registry(self):
        """Wrap existing tools in BaseTool classes"""
        # Wrap read_only tools
        for tool_func in self.read_only:
            wrapped = self._wrap_function_tool(tool_func)
            self.tool_registry.register(wrapped)

        # Wrap modification tools
        for tool_func in self.modification:
            wrapped = self._wrap_function_tool(tool_func)
            self.tool_registry.register(wrapped)

    async def _execute_job_with_agent(self, job: Job) -> str:
        """Execute a job using the main team"""
        # Use existing process_user_request logic
        # but adapted for job execution

        # Set current job context
        for tool in self.tool_registry._tools.values():
            if hasattr(tool, 'set_job_context'):
                tool.set_job_context(job.id)

        # Run the task
        result = await self._run_task_stream(job.task, job.context)

        return result

    async def _on_cron_trigger(self, cron_job: CronJob):
        """Handle cron job trigger by submitting to job queue"""
        priority = JobPriority[cron_job.priority]
        await self.job_orchestrator.submit_job(
            task=cron_job.task,
            priority=priority,
            context={"source": "cron", "cron_job_id": cron_job.id}
        )

    def _create_isolated_orchestrator(self, tools: ToolRegistry, max_iterations: int):
        """Factory for creating isolated orchestrators for subagents"""
        # Create a minimal orchestrator with isolated tools
        # ... (implementation)
        pass

    async def run_isolated_task(self, task: str) -> str:
        """Run a task in isolation (for subagents)"""
        # Execute task without full UI/state management
        # ... (implementation)
        pass
```

### 6.2 Modificar CLI para Jobs

**Archivo**: `src/main.py` (añadir comandos)

```python
class CodeAgentCLI:
    # ... existing code ...

    async def cmd_jobs_list(self):
        """List all jobs"""
        jobs = await self.orchestrator.job_orchestrator.queue._jobs_by_id.values()
        for job in jobs:
            print(f"{job.id}: {job.status.value} - {job.task[:50]}")

    async def cmd_jobs_submit(self, task: str, priority: str = "NORMAL"):
        """Submit a new job"""
        job_id = await self.orchestrator.job_orchestrator.submit_job(
            task=task,
            priority=JobPriority[priority],
        )
        print(f"Job submitted: {job_id}")

    async def cmd_cron_add(self, name: str, schedule: str, task: str):
        """Add a cron job"""
        # Parse schedule and add job
        # ... (implementation)
        pass

    async def cmd_cron_list(self):
        """List cron jobs"""
        jobs = self.orchestrator.cron_service.list_jobs()
        for job in jobs:
            print(f"{job['id']}: {job['name']} - Next run: {job['next_run']}")
```

---

## Archivos Críticos

### Nuevos Archivos (MÍNIMOS para Phase 1)

1. **`src/subagents/events.py`** - Event bus para subagents (100 líneas)
2. **`src/subagents/manager.py`** - SubAgent manager con asyncio.Task (150 líneas)
3. **`src/subagents/tool_wrapper.py`** - Helper para filtrar tools (30 líneas)
4. **`src/tools/spawn_subagent.py`** - Spawn tool (60 líneas)

### Archivos a Modificar (CAMBIOS MÍNIMOS)

1. **`src/config/orchestrator.py`** (~100 líneas añadidas)
   - Añadir inicialización de SubAgentManager
   - Añadir factory method `_create_subagent_orchestrator()`
   - Añadir method `run_task()` para compartir lógica
   - Añadir event subscribers
   - Añadir spawn_subagent a tools del coder

2. **`src/main.py`** (~30 líneas añadidas)
   - Añadir comandos `subagents_list` y `subagent_status`

**TOTAL**: ~370 líneas de código nuevo, ~130 líneas modificadas

---

## Estrategia de Implementación (SIMPLIFICADA)

### Orden Recomendado (Phase 1 - MVP)

1. **Fase 1**: Event Bus (80 líneas)
   - Crear `src/subagents/events.py`
   - Test: Publicar y subscribir eventos

2. **Fase 2**: Tool Wrapper (30 líneas)
   - Crear `src/subagents/tool_wrapper.py`
   - Test: Filtrar lista de tools

3. **Fase 3**: SubAgent Manager (150 líneas) - **CORE**
   - Crear `src/subagents/manager.py`
   - Test: Spawning y cleanup de asyncio.Task

4. **Fase 4**: Spawn Tool (60 líneas)
   - Crear `src/tools/spawn_subagent.py`
   - Test: Llamar spawn desde código

5. **Fase 5**: Integración con Orchestrator (130 líneas modificadas)
   - Modificar `src/config/orchestrator.py`
   - Añadir factory pattern, event handlers
   - Test: Ejecutar tarea principal con spawn

6. **Fase 6**: CLI Commands (30 líneas)
   - Modificar `src/main.py`
   - Añadir comandos de inspección
   - Test: Listar subagents activos

### Testing Incremental

**Después de cada fase**:
- ✅ Unit tests para el componente nuevo
- ✅ Verificar que main flow sigue funcionando
- ✅ Probar integración con fase anterior

**Tests críticos**:
1. Spawn 3 subagents en paralelo → todos completan
2. Subagent falla → parent recibe error event
3. Main task termina → subagents se cancelan
4. Subagent no puede hacer spawn recursivo

---

## Beneficios Esperados (Phase 1)

1. **✅ Ejecución Paralela**: Agente puede hacer spawn de 3+ subagents simultáneos
2. **✅ Aislamiento**: Subagents tienen tools limitados (no spawn recursivo)
3. **✅ Event-driven**: Parent recibe notificaciones cuando subagent completa
4. **✅ No-blocking**: Main agent sigue trabajando mientras subagents corren
5. **✅ Estado aislado**: Cada subagent tiene su propia instancia de orchestrator
6. **✅ Backward compatible**: Sistema existente sigue funcionando exactamente igual
7. **✅ Minimal overhead**: Solo ~370 líneas de código nuevo

### Ejemplo de Uso

```python
# El agente principal puede hacer:
result1 = await spawn_subagent(
    task="Analizar todos los archivos en src/tools/ y generar resumen",
    label="tools analyzer"
)

result2 = await spawn_subagent(
    task="Ejecutar todos los tests y reportar fallos",
    label="test runner"
)

result3 = await spawn_subagent(
    task="Generar documentación para módulo de config",
    label="docs generator"
)

# Mientras los 3 subagents corren en paralelo,
# el agente principal puede seguir con otras tareas
# Cuando cada subagent termina, se publica un evento
# que el parent puede procesar
```

---

## Riesgos y Mitigaciones (Phase 1)

| Riesgo | Mitigación |
|--------|------------|
| Romper funcionalidad existente | ✅ Integración mínima, spawn_subagent es opcional, sistema funciona sin usarlo |
| Spawn recursivo infinito | ✅ Filtrar spawn_subagent de tools de subagents |
| Deadlocks entre subagents | ✅ Subagents no comparten estado, cada uno tiene su orchestrator |
| Memory leaks (tasks no cleanup) | ✅ Done callbacks para auto-cleanup en _running_tasks |
| Subagent falla silenciosamente | ✅ Event bus publica "failed" events, try/except en _run_subagent |
| Max iterations muy alto | ✅ Hardcoded a 15 (vs 25 del main), previene loops largos |
| Factory method crea orchestrator mal configurado | ✅ Tests de integración, verificar que mode="subagent" funciona |

---

## Próximos Pasos (Implementation Roadmap)

### Milestone 1: MVP Funcional (~2-3 horas de implementación)

1. **Crear archivos base** (30 min)
   - `src/subagents/events.py`
   - `src/subagents/tool_wrapper.py`
   - `src/subagents/manager.py`
   - `src/tools/spawn_subagent.py`

2. **Modificar orchestrator** (60 min)
   - Factory method
   - Event subscribers
   - Inicialización de SubAgentManager
   - Añadir spawn_subagent a tools

3. **Testing básico** (30 min)
   - Unit tests para SubAgentManager
   - Integration test: spawn 1 subagent
   - Verificar eventos se publican correctamente

4. **CLI commands** (15 min)
   - `subagents_list`
   - `subagent_status`

5. **Testing avanzado** (45 min)
   - Spawn 3 subagents en paralelo
   - Subagent con error
   - Verificar aislamiento de tools
   - Performance test

### Milestone 2: Refinamiento (opcional, futuro)

- Añadir métricas (tiempo de ejecución, resource usage)
- UI mejorado para mostrar subagents en real-time
- Logging estructurado de eventos
- Documentación de usuario

### Milestone 3: Job Queue System (FUTURO - no Phase 1)

- Implementar JobOrchestrator completo
- Priority queue
- Worker pool
- Cron scheduler

---

## Decisión Final: GO/NO-GO

**Recomendación**: ✅ **GO** con Phase 1 (MVP de subagents paralelos)

**Razones**:
- Scope pequeño (~500 líneas total)
- Integración mínima (bajo riesgo)
- Alto valor (paralelización real)
- Backward compatible
- Fácil de testear incrementalmente

**No incluir en Phase 1**:
- ❌ Job queue (complejidad innecesaria para MVP)
- ❌ Cron scheduler (no prioritario)
- ❌ Message bus completo (solo lo mínimo)
- ❌ Tool registry refactor (wrapper es suficiente)
