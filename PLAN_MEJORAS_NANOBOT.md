# Plan de Mejoras Inspiradas en Nanobot

## 🎯 Objetivos

Implementar las mejoras clave de Nanobot en CodeAgent:

### ✅ Ya Implementado
- [x] Sistema de subagentes paralelos
- [x] Event bus básico
- [x] spawn_subagent tool
- [x] check_subagent_results tool
- [x] **FASE 1: CLI Improvements (2026-02-17)** - Ver [FASE1_CLI_IMPROVEMENTS_COMPLETE.md](FASE1_CLI_IMPROVEMENTS_COMPLETE.md)
- [x] **FASE 2: Cron System (2026-02-17)** - Ver [FASE2_CRON_SYSTEM_COMPLETE.md](FASE2_CRON_SYSTEM_COMPLETE.md)

### 🚀 A Implementar (Por Prioridad)

## ✅ FASE 1: CLI Improvements - COMPLETADO

**Estado**: ✅ Completado el 2026-02-17
**Documentación**: [FASE1_CLI_IMPROVEMENTS_COMPLETE.md](FASE1_CLI_IMPROVEMENTS_COMPLETE.md)
**Tests**: 6/6 passing

**Implementado**:
- ✅ Terminal state recovery con termios
- ✅ HTML formatted prompts
- ✅ patch_stdout integration
- ✅ TTY input flushing
- ✅ Signal handlers (SIGINT/SIGTERM)
- ✅ Cross-platform support

**Pendiente para futuro**:
- ⏳ Migrar a Typer (opcional, baja prioridad)

---

## ✅ FASE 2: Cron System - COMPLETADO

**Estado**: ✅ Completado el 2026-02-17
**Documentación**: [FASE2_CRON_SYSTEM_COMPLETE.md](FASE2_CRON_SYSTEM_COMPLETE.md)
**Tests**: 7/7 passing

**Implementado**:
- ✅ 3 tipos de schedule: at (one-time), every (interval), cron (expression)
- ✅ CronService con asyncio timers
- ✅ JSON persistence
- ✅ CLI commands (/cron add/list/enable/disable/remove/run)
- ✅ Integración completa con subagentes
- ✅ Automatic job execution via subagent spawning

---

## FASE 1 ORIGINAL: CLI Improvements (Alta Prioridad - Quick Wins)

### 1.1 Migrar a Typer ⭐⭐⭐
**Impacto**: Alto | **Esfuerzo**: 2-3 horas

**Beneficios**:
- CLI más limpia y declarativa
- 40% menos código
- Help automático mejorado
- Subcomandos organizados
- `typer.confirm()` y `typer.prompt()` nativos

**Archivos a modificar**:
- `src/cli.py` (138 líneas → ~80 líneas con Typer)
- `src/main.py` (agregar subcomandos)

**Implementación**:
```python
# src/cli.py - NUEVO con Typer
import typer
from typing import Optional

app = typer.Typer(
    name="daveagent",
    help="DaveAgent - AI-powered coding assistant",
    add_completion=False,
)

# Subapps para organizar comandos
config_app = typer.Typer(help="Configuration commands")
subagent_app = typer.Typer(help="Subagent management")
cron_app = typer.Typer(help="Scheduled tasks")

app.add_typer(config_app, name="config")
app.add_typer(subagent_app, name="subagent")
app.add_typer(cron_app, name="cron")

@app.command()
def chat(
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Debug mode"),
):
    """Start interactive chat session."""
    # ... implementation ...

@config_app.command("show")
def config_show():
    """Show current configuration."""
    # ...

@config_app.command("set-model")
def config_set_model(
    model: str = typer.Argument(..., help="Model name")
):
    """Change LLM model."""
    # ...

@subagent_app.command("list")
def subagent_list(
    all: bool = typer.Option(False, "--all", "-a", help="Show all (including completed)")
):
    """List active subagents."""
    # ...

@subagent_app.command("status")
def subagent_status(
    subagent_id: str = typer.Argument(..., help="Subagent ID")
):
    """Show detailed status of a subagent."""
    # ...

@cron_app.command("add")
def cron_add(
    name: str = typer.Argument(..., help="Job name"),
    task: str = typer.Option(..., "--task", "-t", help="Task description"),
    every: Optional[int] = typer.Option(None, "--every", help="Interval in seconds"),
    cron_expr: Optional[str] = typer.Option(None, "--cron", help="Cron expression"),
    at: Optional[str] = typer.Option(None, "--at", help="One-time execution timestamp"),
):
    """Add a scheduled task."""
    # ...

@cron_app.command("list")
def cron_list():
    """List all scheduled tasks."""
    # ...
```

### 1.2 HTML Formatted Prompts ⭐⭐
**Impacto**: Medio | **Esfuerzo**: 1 hora

**Archivos a modificar**:
- `src/interfaces/cli_interface.py:146-176` (get_user_input)

**Implementación**:
```python
# src/interfaces/cli_interface.py
from prompt_toolkit.formatted_text import HTML

async def get_user_input(self, prompt: str = "") -> str:
    if not prompt:
        mode_indicator = "🔧" if self.current_mode == "agent" else "💬"
        mode_text = self.current_mode.upper()

        # ANTES: prompt = f"[{mode_indicator} {mode_text}] You: "
        # DESPUÉS: HTML formatted
        prompt = HTML(
            f"<b fg='cyan'>[{mode_indicator}]</b> "
            f"<b fg='ansiyellow'>{mode_text}</b> "
            f"<b>You:</b> "
        )

    try:
        loop = asyncio.get_event_loop()
        with patch_stdout():  # AÑADIR (ver 1.4)
            user_input = await loop.run_in_executor(
                None,
                lambda: self.session.prompt(prompt)
            )
        # ...
```

### 1.3 Terminal State Recovery ⭐⭐⭐
**Impacto**: Alto | **Esfuerzo**: 1.5 horas

**Archivos a modificar**:
- `src/interfaces/cli_interface.py:27-44` (__init__)
- Agregar métodos de terminal management

**Implementación**:
```python
# src/interfaces/cli_interface.py
import sys
import os
import termios
import signal

class CLIInterface:
    def __init__(self):
        # ... existing code ...

        # NEW: Terminal state management
        self._saved_term_attrs = None
        self._save_terminal_state()

        # Setup signal handlers for cleanup
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_terminate)

    def _save_terminal_state(self):
        """Save terminal attributes for later recovery."""
        try:
            if os.isatty(sys.stdin.fileno()):
                self._saved_term_attrs = termios.tcgetattr(sys.stdin.fileno())
        except Exception:
            pass

    def _restore_terminal_state(self):
        """Restore terminal to original state."""
        if self._saved_term_attrs:
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,
                    self._saved_term_attrs
                )
            except Exception:
                pass

    def _flush_pending_tty_input(self):
        """Drop unread keypresses typed while model was generating."""
        try:
            fd = sys.stdin.fileno()
            if not os.isatty(fd):
                return
            termios.tcflush(fd, termios.TCIFLUSH)
        except Exception:
            pass

    def _handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self._restore_terminal_state()
        print("\n\n👋 Interrupted by user")
        sys.exit(0)

    def _handle_terminate(self, signum, frame):
        """Handle termination signal."""
        self._restore_terminal_state()
        sys.exit(0)

    def __del__(self):
        """Cleanup on destruction."""
        self._restore_terminal_state()
```

### 1.4 patch_stdout para evitar conflictos ⭐⭐
**Impacto**: Medio | **Esfuerzo**: 30 min

**Archivos a modificar**:
- `src/interfaces/cli_interface.py:146-176` (get_user_input)
- `src/interfaces/cli_interface.py:177-254` (_process_file_mentions)

**Implementación**:
```python
from prompt_toolkit.patch_stdout import patch_stdout

async def get_user_input(self, prompt: str = "") -> str:
    # ...
    try:
        loop = asyncio.get_event_loop()

        # Flush pending input before prompting
        self._flush_pending_tty_input()

        # Use patch_stdout to prevent output conflicts
        with patch_stdout():
            user_input = await loop.run_in_executor(
                None,
                lambda: self.session.prompt(prompt)
            )

        # ...
    except (EOFError, KeyboardInterrupt):
        self._restore_terminal_state()
        return "/exit"
```

---

## FASE 2: Cron System (Media Prioridad)

### 2.1 Tipos de Datos Cron ⭐⭐⭐
**Impacto**: Alto | **Esfuerzo**: 1 hora

**Archivo nuevo**: `src/cron/types.py`

```python
from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime

@dataclass
class CronSchedule:
    """Schedule configuration for cron jobs."""
    kind: Literal["at", "every", "cron"]
    at_ms: int | None = None        # Unix timestamp in ms for "at"
    every_ms: int | None = None      # Interval in ms for "every"
    expr: str | None = None          # Cron expression for "cron"
    tz: str | None = None           # Timezone for cron expressions

@dataclass
class CronJobState:
    """Runtime state of a cron job."""
    next_run_at_ms: int | None = None
    last_run_at_ms: int | None = None
    last_status: str = "idle"  # "idle", "ok", "error"
    last_error: str | None = None
    run_count: int = 0

@dataclass
class CronJob:
    """Cron job definition."""
    id: str
    name: str
    enabled: bool
    schedule: CronSchedule
    task: str  # Task description to execute
    priority: str = "NORMAL"
    state: CronJobState = field(default_factory=CronJobState)
    created_at_ms: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    delete_after_run: bool = False  # Auto-delete after one-time execution
```

### 2.2 Cron Service ⭐⭐⭐
**Impacto**: Alto | **Esfuerzo**: 3 horas

**Archivo nuevo**: `src/cron/service.py`

```python
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Callable
from .types import CronJob, CronSchedule, CronJobState

class CronService:
    """
    Cron service for scheduled task execution.

    Supports 3 schedule types:
    - at: One-time execution at specific timestamp
    - every: Periodic execution at interval
    - cron: Cron expression-based scheduling
    """

    def __init__(
        self,
        storage_path: Path,
        on_job: Callable[[CronJob], None],  # Callback when job triggers
    ):
        self.storage_path = storage_path
        self.on_job = on_job
        self._jobs: list[CronJob] = []
        self._timer_task: asyncio.Task | None = None
        self._running = False

        # Load existing jobs
        self._load_jobs()

    def add_job(
        self,
        name: str,
        schedule: CronSchedule,
        task: str,
        priority: str = "NORMAL"
    ) -> str:
        """Add a new cron job."""
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
            state=CronJobState(next_run_at_ms=next_run),
            created_at_ms=now_ms,
            delete_after_run=(schedule.kind == "at"),
        )

        self._jobs.append(job)
        self._save_jobs()

        if self._running:
            self._arm_timer()

        return job_id

    def enable_job(self, job_id: str, enabled: bool = True) -> bool:
        """Enable or disable a job."""
        for job in self._jobs:
            if job.id == job_id:
                job.enabled = enabled
                self._save_jobs()
                if self._running:
                    self._arm_timer()
                return True
        return False

    def remove_job(self, job_id: str) -> bool:
        """Remove a cron job."""
        before = len(self._jobs)
        self._jobs = [j for j in self._jobs if j.id != job_id]

        if len(self._jobs) < before:
            self._save_jobs()
            if self._running:
                self._arm_timer()
            return True
        return False

    def list_jobs(self, enabled_only: bool = False) -> list[dict]:
        """List all jobs."""
        jobs = self._jobs if not enabled_only else [j for j in self._jobs if j.enabled]

        return [
            {
                "id": j.id,
                "name": j.name,
                "enabled": j.enabled,
                "schedule": self._format_schedule(j.schedule),
                "task": j.task,
                "next_run": datetime.fromtimestamp(j.state.next_run_at_ms / 1000) if j.state.next_run_at_ms else None,
                "last_run": datetime.fromtimestamp(j.state.last_run_at_ms / 1000) if j.state.last_run_at_ms else None,
                "run_count": j.state.run_count,
                "status": j.state.last_status,
            }
            for j in jobs
        ]

    async def start(self):
        """Start the cron service."""
        self._running = True
        self._arm_timer()

    def stop(self):
        """Stop the cron service."""
        self._running = False
        if self._timer_task:
            self._timer_task.cancel()

    def _compute_next_run(self, schedule: CronSchedule, now_ms: int) -> int | None:
        """Compute next run time in milliseconds."""
        if schedule.kind == "at":
            return schedule.at_ms if schedule.at_ms and schedule.at_ms > now_ms else None

        if schedule.kind == "every":
            return now_ms + schedule.every_ms if schedule.every_ms else None

        if schedule.kind == "cron" and schedule.expr:
            try:
                from croniter import croniter
                from zoneinfo import ZoneInfo

                tz = ZoneInfo(schedule.tz) if schedule.tz else None
                base_dt = datetime.fromtimestamp(now_ms / 1000, tz=tz)
                cron = croniter(schedule.expr, base_dt)
                next_dt = cron.get_next(datetime)
                return int(next_dt.timestamp() * 1000)
            except Exception as e:
                print(f"Error computing cron next run: {e}")
                return None

        return None

    def _arm_timer(self):
        """Set timer for next job execution."""
        if self._timer_task:
            self._timer_task.cancel()

        # Find next enabled job
        enabled_jobs = [
            j for j in self._jobs
            if j.enabled and j.state.next_run_at_ms
        ]

        if not enabled_jobs:
            return

        # Get job with earliest next_run
        next_job = min(enabled_jobs, key=lambda j: j.state.next_run_at_ms)
        now_ms = int(datetime.now().timestamp() * 1000)
        delay_s = max(0, (next_job.state.next_run_at_ms - now_ms) / 1000)

        async def timer_tick():
            await asyncio.sleep(delay_s)
            if self._running:
                await self._on_timer()

        self._timer_task = asyncio.create_task(timer_tick())

    async def _on_timer(self):
        """Handle timer tick - execute due jobs."""
        now_ms = int(datetime.now().timestamp() * 1000)

        # Find all jobs due for execution
        due_jobs = [
            j for j in self._jobs
            if j.enabled
            and j.state.next_run_at_ms
            and now_ms >= j.state.next_run_at_ms
        ]

        # Execute each due job
        for job in due_jobs:
            await self._execute_job(job)

        # Re-arm timer for next execution
        self._arm_timer()

    async def _execute_job(self, job: CronJob):
        """Execute a cron job."""
        now_ms = int(datetime.now().timestamp() * 1000)

        try:
            # Call callback
            await self.on_job(job)

            job.state.last_status = "ok"
            job.state.last_error = None
        except Exception as e:
            job.state.last_status = "error"
            job.state.last_error = str(e)

        # Update state
        job.state.last_run_at_ms = now_ms
        job.state.run_count += 1

        # Handle one-time jobs
        if job.schedule.kind == "at":
            if job.delete_after_run:
                self._jobs.remove(job)
            else:
                job.enabled = False
                job.state.next_run_at_ms = None
        else:
            # Compute next run
            job.state.next_run_at_ms = self._compute_next_run(job.schedule, now_ms)

        self._save_jobs()

    def _format_schedule(self, schedule: CronSchedule) -> str:
        """Format schedule for display."""
        if schedule.kind == "at":
            dt = datetime.fromtimestamp(schedule.at_ms / 1000)
            return f"at {dt.strftime('%Y-%m-%d %H:%M:%S')}"

        if schedule.kind == "every":
            seconds = schedule.every_ms / 1000
            if seconds >= 86400:
                return f"every {seconds/86400:.1f} days"
            elif seconds >= 3600:
                return f"every {seconds/3600:.1f} hours"
            elif seconds >= 60:
                return f"every {seconds/60:.1f} minutes"
            else:
                return f"every {seconds:.1f} seconds"

        if schedule.kind == "cron":
            return f"cron: {schedule.expr}"

        return "unknown"

    def _load_jobs(self):
        """Load jobs from JSON storage."""
        if not self.storage_path.exists():
            return

        try:
            data = json.loads(self.storage_path.read_text())
            # TODO: Deserialize JSON to CronJob objects
            # self._jobs = ...
        except Exception as e:
            print(f"Error loading cron jobs: {e}")

    def _save_jobs(self):
        """Save jobs to JSON storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # TODO: Serialize CronJob objects to JSON
            data = {}
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving cron jobs: {e}")
```

### 2.3 Integración con Orchestrator ⭐⭐
**Impacto**: Medio | **Esfuerzo**: 1 hora

**Archivo a modificar**: `src/config/orchestrator.py`

```python
# En __init__ de AgentOrchestrator
from src.cron import CronService
from pathlib import Path

# Initialize cron service
cron_storage = Path(".daveagent/cron/jobs.json")
self.cron_service = CronService(
    storage_path=cron_storage,
    on_job=self._on_cron_job_trigger,
)

async def _on_cron_job_trigger(self, cron_job):
    """Handle cron job trigger by spawning subagent."""
    # Spawn subagent to execute the cron job task
    await self.subagent_manager.spawn(
        task=cron_job.task,
        label=f"cron-{cron_job.name}",
        parent_task_id="cron",
        max_iterations=15,
    )
```

---

## FASE 3: Auto-Injection de Resultados (Alta Prioridad)

### 3.1 Modificar Callbacks para Inyección Automática ⭐⭐⭐
**Impacto**: Alto | **Esfuerzo**: 2 horas

**Objetivo**: Que los resultados de subagents se inyecten automáticamente en la conversación del agente principal, similar a Nanobot.

**Archivos a modificar**:
- `src/config/orchestrator.py` (callbacks de eventos)
- `src/config/prompts.py` (agregar instrucción de auto-check)

**Implementación Opción 1 - Auto-injection como mensaje del sistema**:
```python
# src/config/orchestrator.py

async def _on_subagent_completed(self, event) -> None:
    """Handle subagent completion - inject result into main conversation."""
    label = event.content.get('label', 'unknown')
    result = event.content.get('result', '')
    task = event.content.get('task', '')

    # Log to console
    self.cli.print_success(f"✓ Subagent '{label}' completed")

    # NANOBOT-STYLE: Inject result as system message
    system_message = f"""[Background Task Completed: '{label}']

Task: {task}

Result:
{result}

---
Summarize this result naturally for the user in 1-2 sentences.
Focus on key findings. Don't mention "subagent" or technical terms."""

    # Add to coder agent's message history
    # This makes the agent "see" the result automatically
    if hasattr(self, 'coder_agent') and hasattr(self.coder_agent, '_messages'):
        self.coder_agent._messages.append({
            "role": "system",
            "content": system_message
        })

    # Trigger agent to process the result
    # This makes the agent respond with the summary
    if hasattr(self, '_process_background_result'):
        await self._process_background_result(system_message)
```

**Implementación Opción 2 - Periodic auto-check con instrucción en prompt**:
```python
# src/config/prompts.py - Agregar a AGENT_SYSTEM_PROMPT

<subagent_system>
**PARALLEL TASK EXECUTION WITH SUBAGENTS**

... (existing content) ...

**CRITICAL: AUTO-CHECK FOR RESULTS**
After spawning subagents, you MUST periodically call check_subagent_results:
- Call it after spawning (to see if quick tasks completed immediately)
- Call it after waiting a reasonable time
- Call it before responding to user about task status
- The tool will return announcements that you must summarize naturally

Example flow:
1. User asks: "Analyze file1 and file2"
2. You spawn 2 subagents
3. You call check_subagent_results after 5 seconds
4. You receive results and summarize: "File1 contains..."
</subagent_system>
```

---

## FASE 4: Typer CLI Commands para Cron

### 4.1 Comandos Cron con Typer ⭐⭐
**Impacto**: Medio | **Esfuerzo**: 1 hora

**Implementación en CLI** (asumiendo migración a Typer):

```python
# src/cli.py

@cron_app.command("add")
def cron_add(
    name: str = typer.Argument(..., help="Job name"),
    task: str = typer.Option(..., "--task", "-t", help="Task description"),
    every: Optional[int] = typer.Option(None, "--every", help="Interval in seconds"),
    cron_expr: Optional[str] = typer.Option(None, "--cron", help="Cron expression (e.g., '0 9 * * *')"),
    at: Optional[str] = typer.Option(None, "--at", help="One-time execution (ISO format: 2024-01-15T09:00:00)"),
    priority: str = typer.Option("NORMAL", "--priority", help="Job priority"),
):
    """Add a scheduled task."""
    from src.cron.types import CronSchedule
    from src.config.orchestrator import get_orchestrator  # Singleton
    from datetime import datetime

    # Validate: exactly one schedule type must be provided
    schedule_types = sum([every is not None, cron_expr is not None, at is not None])
    if schedule_types != 1:
        typer.echo("Error: Provide exactly one of --every, --cron, or --at", err=True)
        raise typer.Exit(1)

    # Create schedule
    if every is not None:
        schedule = CronSchedule(kind="every", every_ms=every * 1000)
    elif cron_expr is not None:
        schedule = CronSchedule(kind="cron", expr=cron_expr)
    elif at is not None:
        try:
            dt = datetime.fromisoformat(at)
            schedule = CronSchedule(kind="at", at_ms=int(dt.timestamp() * 1000))
        except ValueError:
            typer.echo(f"Error: Invalid datetime format: {at}", err=True)
            typer.echo("Use ISO format: 2024-01-15T09:00:00", err=True)
            raise typer.Exit(1)

    # Add job
    orch = get_orchestrator()
    job_id = orch.cron_service.add_job(name, schedule, task, priority)

    typer.echo(f"✓ Cron job '{name}' added (ID: {job_id})")
    typer.echo(f"  Schedule: {orch.cron_service._format_schedule(schedule)}")
    typer.echo(f"  Task: {task}")

@cron_app.command("list")
def cron_list(
    all: bool = typer.Option(False, "--all", "-a", help="Show all jobs (including disabled)")
):
    """List scheduled tasks."""
    from rich.table import Table
    from rich.console import Console
    from src.config.orchestrator import get_orchestrator

    orch = get_orchestrator()
    jobs = orch.cron_service.list_jobs(enabled_only=not all)

    if not jobs:
        typer.echo("No cron jobs found")
        return

    # Rich table
    table = Table(title="Scheduled Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Enabled")
    table.add_column("Schedule")
    table.add_column("Next Run")
    table.add_column("Runs")
    table.add_column("Status")

    for job in jobs:
        table.add_row(
            job["id"],
            job["name"],
            "✓" if job["enabled"] else "✗",
            job["schedule"],
            job["next_run"].strftime("%Y-%m-%d %H:%M") if job["next_run"] else "-",
            str(job["run_count"]),
            job["status"]
        )

    console = Console()
    console.print(table)

@cron_app.command("enable")
def cron_enable(
    job_id: str = typer.Argument(..., help="Job ID"),
    disable: bool = typer.Option(False, "--disable", help="Disable instead of enable"),
):
    """Enable or disable a scheduled task."""
    from src.config.orchestrator import get_orchestrator

    orch = get_orchestrator()
    success = orch.cron_service.enable_job(job_id, enabled=not disable)

    if success:
        action = "disabled" if disable else "enabled"
        typer.echo(f"✓ Job {job_id} {action}")
    else:
        typer.echo(f"Error: Job {job_id} not found", err=True)
        raise typer.Exit(1)

@cron_app.command("remove")
def cron_remove(
    job_id: str = typer.Argument(..., help="Job ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a scheduled task."""
    from src.config.orchestrator import get_orchestrator

    if not force:
        confirmed = typer.confirm(f"Remove job {job_id}?")
        if not confirmed:
            raise typer.Abort()

    orch = get_orchestrator()
    success = orch.cron_service.remove_job(job_id)

    if success:
        typer.echo(f"✓ Job {job_id} removed")
    else:
        typer.echo(f"Error: Job {job_id} not found", err=True)
        raise typer.Exit(1)

@cron_app.command("run")
def cron_run(
    job_id: str = typer.Argument(..., help="Job ID"),
):
    """Manually trigger a scheduled task."""
    # TODO: Implement manual job trigger
    pass
```

---

## Roadmap de Implementación

### Sprint 1 (1 semana) - CLI Improvements
- [ ] Día 1-2: Migrar a Typer
- [ ] Día 3: HTML formatted prompts
- [ ] Día 4: Terminal state recovery
- [ ] Día 5: Testing y refinamiento

### Sprint 2 (1 semana) - Cron System
- [ ] Día 1: Tipos y estructura de datos
- [ ] Día 2-3: CronService implementation
- [ ] Día 4: Integración con orchestrator
- [ ] Día 5: CLI commands con Typer

### Sprint 3 (3 días) - Auto-injection
- [ ] Día 1: Modificar callbacks
- [ ] Día 2: Testing comportamiento Nanobot
- [ ] Día 3: Documentación

---

## Dependencias Nuevas

```toml
# Agregar a pyproject.toml o requirements.txt
typer>=0.9.0                 # CLI framework
croniter>=2.0.0              # Cron expression parsing
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_cron_service.py
def test_cron_every_schedule():
    schedule = CronSchedule(kind="every", every_ms=60000)  # 1 minute
    service = CronService(...)
    next_run = service._compute_next_run(schedule, now_ms)
    assert next_run == now_ms + 60000

def test_cron_at_schedule():
    future_ms = int((datetime.now() + timedelta(hours=1)).timestamp() * 1000)
    schedule = CronSchedule(kind="at", at_ms=future_ms)
    # ...

def test_cron_expression():
    schedule = CronSchedule(kind="cron", expr="0 9 * * *")  # 9am daily
    # ...
```

### Integration Tests
```python
# tests/test_subagent_auto_injection.py
async def test_subagent_result_auto_injection():
    # Spawn subagent
    await spawn_subagent(task="test task", label="tester")

    # Wait for completion
    await asyncio.sleep(5)

    # Verify result was injected into conversation
    assert any("Background Task Completed" in msg for msg in agent.messages)
```

---

## Prioridad de Implementación

### MUST HAVE (Sprint 1)
1. ✅ Migrar a Typer
2. ✅ Terminal state recovery
3. ✅ HTML formatted prompts

### SHOULD HAVE (Sprint 2)
4. ✅ Cron system (at/every/cron)
5. ✅ CLI commands para cron

### NICE TO HAVE (Sprint 3)
6. ✅ Auto-injection de resultados
7. ⚠️ Advanced cron features (timezone support, etc.)

---

## Métricas de Éxito

- [ ] CLI tiene 40% menos código con Typer
- [ ] Terminal se restaura correctamente en ctrl+C
- [ ] Prompts se ven mejor con colores HTML
- [ ] Cron jobs se ejecutan en schedule exacto
- [ ] Resultados de subagents se inyectan automáticamente
- [ ] Tests pasan 100%
- [ ] Documentación completa
