"""
Interfaz CLI interactiva al estilo Claude Code
"""
import asyncio
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from datetime import datetime
import sys
from pathlib import Path


class CLIInterface:
    """Interfaz CLI rica e interactiva para el agente de código"""

    def __init__(self):
        self.console = Console()
        self.session = PromptSession(
            history=FileHistory(".agent_history"),
            auto_suggest=AutoSuggestFromHistory(),
        )
        self.conversation_active = False

    def print_banner(self):
        """Muestra el banner de bienvenida"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ██████╗ ██████╗ ███████╗     █████╗  ██████╗     ║
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔════╝     ║
║  ██║     ██║   ██║██║  ██║█████╗      ███████║██║  ███╗    ║
║  ██║     ██║   ██║██║  ██║██╔══╝      ██╔══██║██║   ██║    ║
║  ╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║╚██████╔╝    ║
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝ ╚═════╝     ║
║                                                              ║
║              Agente Inteligente de Desarrollo               ║
║                    Versión 1.0.0                            ║
╚══════════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
        self.console.print()

    def print_welcome_message(self):
        """Muestra el mensaje de bienvenida"""
        welcome = """
Bienvenido al Agente de Código Inteligente

Este agente puede ayudarte a:
  • Analizar y comprender código
  • Implementar nuevas funcionalidades
  • Corregir errores y bugs
  • Refactorizar código existente
  • Ejecutar comandos y scripts
  • Buscar y modificar archivos

**Comandos disponibles:**
  • `/help` - Muestra la ayuda
  • `/new` - Inicia una nueva conversación sin historial
  • `/clear` - Limpia el historial de conversación
  • `/plan` - Muestra el plan de ejecución actual
  • `/stats` - Muestra estadísticas de la sesión
  • `/exit` o `/quit` - Salir del agente

Simplemente describe lo que necesitas y el agente creará un plan y lo ejecutará.
        """
        self.console.print(Panel(Markdown(welcome), title="Información", border_style="green"))
        self.console.print()

    async def get_user_input(self, prompt: str = "") -> str:
        """
        Obtiene input del usuario de manera asíncrona

        Args:
            prompt: Texto del prompt

        Returns:
            Input del usuario
        """
        if not prompt:
            prompt = "Tu: "

        try:
            # Ejecutar el prompt en un executor para no bloquear el loop
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(
                None,
                lambda: self.session.prompt(prompt)
            )
            return user_input.strip()
        except (EOFError, KeyboardInterrupt):
            return "/exit"

    def print_user_message(self, message: str):
        """Muestra un mensaje del usuario"""
        self.console.print()
        self.console.print(f"[bold blue]Tu:[/bold blue] {message}")
        self.console.print()

    def print_agent_message(self, message: str, agent_name: str = "Agente"):
        """Muestra un mensaje del agente"""
        self.console.print(f"[bold green]{agent_name}:[/bold green]")
        self.console.print(Panel(Markdown(message), border_style="green"))
        self.console.print()

    def print_plan(self, plan_summary: str):
        """Muestra el plan de ejecución"""
        self.console.print()
        self.console.print(Panel(
            plan_summary,
            title="[bold cyan]Plan de Ejecución[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()

    def print_task_start(self, task_id: int, task_title: str, task_description: str):
        """Muestra que una tarea está comenzando"""
        self.console.print()
        self.console.print(
            f"[bold yellow]⚡ Ejecutando Tarea {task_id}:[/bold yellow] {task_title}",
            style="bold"
        )
        self.console.print(f"   {task_description}", style="dim")
        self.console.print()

    def print_task_complete(self, task_id: int, task_title: str, result_summary: str):
        """Muestra que una tarea se completó"""
        self.console.print()
        self.console.print(
            f"[bold green]✓ Tarea {task_id} Completada:[/bold green] {task_title}"
        )
        if result_summary:
            self.console.print(Panel(
                result_summary,
                border_style="green",
                title="Resultado"
            ))
        self.console.print()

    def print_task_failed(self, task_id: int, task_title: str, error: str):
        """Muestra que una tarea falló"""
        self.console.print()
        self.console.print(
            f"[bold red]✗ Tarea {task_id} Falló:[/bold red] {task_title}"
        )
        self.console.print(Panel(
            error,
            border_style="red",
            title="Error"
        ))
        self.console.print()

    def print_plan_update(self, reasoning: str, changes_summary: str):
        """Muestra que el plan está siendo actualizado"""
        self.console.print()
        self.console.print("[bold yellow]🔄 Actualizando Plan de Ejecución[/bold yellow]")
        self.console.print(Panel(
            f"**Razonamiento:**\n{reasoning}\n\n**Cambios:**\n{changes_summary}",
            border_style="yellow"
        ))
        self.console.print()

    def print_thinking(self, message: str = "Pensando..."):
        """Muestra un indicador de que el agente está pensando"""
        self.console.print(f"[dim]{message}[/dim]")

    def print_error(self, error: str):
        """Muestra un mensaje de error"""
        self.console.print()
        self.console.print(Panel(
            error,
            title="[bold red]Error[/bold red]",
            border_style="red"
        ))
        self.console.print()

    def print_warning(self, warning: str):
        """Muestra un mensaje de advertencia"""
        self.console.print()
        self.console.print(Panel(
            warning,
            title="[bold yellow]Advertencia[/bold yellow]",
            border_style="yellow"
        ))
        self.console.print()

    def print_info(self, info: str, title: str = "Información"):
        """Muestra un mensaje informativo"""
        self.console.print()
        self.console.print(Panel(
            info,
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()

    def print_success(self, message: str):
        """Muestra un mensaje de éxito"""
        self.console.print()
        self.console.print(f"[bold green]✓ {message}[/bold green]")
        self.console.print()

    def create_progress_table(self, tasks: List[dict]) -> Table:
        """Crea una tabla con el progreso de las tareas"""
        table = Table(title="Progreso de Tareas", show_header=True, header_style="bold")
        table.add_column("ID", style="cyan", width=4)
        table.add_column("Estado", width=12)
        table.add_column("Tarea", style="white")

        status_styles = {
            "completed": "[green]✓ Completada[/green]",
            "in_progress": "[yellow]⚡ En progreso[/yellow]",
            "pending": "[dim]○ Pendiente[/dim]",
            "failed": "[red]✗ Fallida[/red]",
            "blocked": "[red]⊘ Bloqueada[/red]"
        }

        for task in tasks:
            table.add_row(
                str(task["id"]),
                status_styles.get(task["status"], task["status"]),
                task["title"]
            )

        return table

    def print_statistics(self, stats: dict):
        """Muestra estadísticas de la sesión"""
        stats_text = f"""
**Estadísticas de la Sesión:**

• Total de mensajes: {stats.get('total_messages', 0)}
• Tokens utilizados: {stats.get('total_tokens', 0)}
• Compresiones realizadas: {stats.get('compressed_count', 0)}
• Tiene resumen: {'Sí' if stats.get('has_summary') else 'No'}
• Necesita compresión: {'Sí' if stats.get('needs_compression') else 'No'}
        """
        self.print_info(stats_text, "Estadísticas")

    def print_help(self):
        """Muestra la ayuda"""
        help_text = """
**Comandos Disponibles:**

• `/help` - Muestra este mensaje de ayuda
• `/new` - Inicia una nueva conversación sin historial
• `/clear` - Limpia el historial de conversación
• `/plan` - Muestra el plan de ejecución actual
• `/stats` - Muestra estadísticas de la sesión
• `/save <archivo>` - Guarda el historial en un archivo
• `/load <archivo>` - Carga un historial desde un archivo
• `/exit` o `/quit` - Salir del agente

**Uso:**

Simplemente escribe lo que necesitas que el agente haga. El agente:
1. Creará un plan de ejecución con tareas
2. Ejecutará cada tarea llamando al agente de código
3. Ajustará el plan si encuentra errores o nueva información
4. Continuará hasta completar el objetivo

**Ejemplos:**

"Crea una API REST con FastAPI que tenga endpoints para usuarios"

"Encuentra todos los archivos Python con bugs y corrígelos"

"Refactoriza el código en src/utils para usar async/await"
        """
        self.print_info(help_text, "Ayuda")

    def print_goodbye(self):
        """Muestra el mensaje de despedida"""
        goodbye = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              Gracias por usar Code Agent                    ║
║                   ¡Hasta pronto!                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        self.console.print()
        self.console.print(goodbye, style="bold cyan")
        self.console.print()

    def clear_screen(self):
        """Limpia la pantalla"""
        self.console.clear()
