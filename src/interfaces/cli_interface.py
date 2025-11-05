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
from src.utils import FileIndexer, select_file_interactive, VibeSpinner
import random
import time

class CLIInterface:
    """Interfaz CLI rica e interactiva para el agente de código"""

    def __init__(self):
        self.console = Console()
        self.session = PromptSession(
            history=FileHistory(".agent_history"),
            auto_suggest=AutoSuggestFromHistory(),
        )
        self.conversation_active = False
        self.file_indexer = None  # Will be initialized on first use
        self.mentioned_files: List[str] = []  # Track files mentioned with @
        self.vibe_spinner: Optional[VibeSpinner] = None  # Spinner for thinking animation

    def print_banner(self):
        """Muestra el banner de bienvenida con una animación de 'partículas'"""
        
        banner_lines = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗  █████╗ ██╗   ██╗███████╗                          ║
║   ██╔══██╗██╔══██╗██║   ██║██╔════╝                          ║
║   ██║  ██║███████║██║   ██║█████╗                            ║
║   ██║  ██║██╔══██║╚██╗ ██╔╝██╔══╝                            ║
║   ██████╔╝██║  ██║ ╚████╔╝ ███████╗                          ║
║   ╚═════╝ ╚═╝  ╚═╝  ╚═══╝  ╚══════╝                          ║ 
║                                                              ║
║    █████╗  ██████╗ ███████╗███╗   ██╗████████╗               ║
║   ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝               ║
║   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║                  ║
║   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║                  ║
║   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║                  ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝                  ║
║                                                              ║
║              Agente Inteligente de Desarrollo                ║
║                    Versión 1.0.1                             ║
╚══════════════════════════════════════════════════════════════╝
        """.strip('\n').split('\n')
        
        height = len(banner_lines)
        width = max(len(line) for line in banner_lines)
        
        # Caracteres a usar como "partículas"
        particles = ['.', ':', '*', '°', '·', ' '] 
        
        # 1. Crear el estado inicial (campo de partículas)
        # Usamos una lista de listas de caracteres para poder mutarla
        current_state = []
        for r in range(height):
            row = []
            for c in range(width):
                # Si hay un caracter en el banner final, poner una partícula
                if c < len(banner_lines[r]) and banner_lines[r][c] != ' ':
                    row.append(random.choice(particles))
                else:
                    row.append(' ') # Mantener los espacios vacíos
            current_state.append(row)

        # 2. Obtener todas las coordenadas (fila, col) de los caracteres reales
        coords = []
        for r in range(height):
            for c in range(width):
                # Solo queremos "resolver" los caracteres que no son espacios
                if c < len(banner_lines[r]) and banner_lines[r][c] != ' ':
                    coords.append((r, c))
        
        # 3. Barajar las coordenadas para un efecto de ensamblado aleatorio
        random.shuffle(coords)
        
        # 4. Configurar la animación con Rich Live
        # Definimos cuántos caracteres revelar por cuadro (más bajo = más lento)
        reveal_per_frame = max(1, len(coords) // 20) # Apunta a ~20 cuadros
        
        with Live(console=self.console, refresh_per_second=15, transient=True) as live:
            # Mostrar el campo de partículas inicial por un momento
            text = Text('\n'.join(''.join(row) for row in current_state), style="bold cyan")
            live.update(text)
            time.sleep(0.3) # Pausa inicial

            # 5. Empezar a revelar los caracteres en lotes
            for i in range(0, len(coords), reveal_per_frame):
                batch = coords[i : i + reveal_per_frame]
                
                for r, c in batch:
                    # Reemplazar la partícula con el caracter correcto
                    current_state[r][c] = banner_lines[r][c]
                
                # Actualizar el Live con el nuevo estado
                text = Text('\n'.join(''.join(row) for row in current_state), style="bold cyan")
                live.update(text)
                time.sleep(0.02) # Pequeña pausa entre cuadros

        # 6. Imprimir el banner final de forma permanente
        # (El Live con transient=True desaparece, así que lo imprimimos de nuevo)
        final_text = Text('\n'.join(banner_lines), style="bold cyan")
        self.console.print(final_text)
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

**Comandos principales:**
  • `/help` - Muestra la ayuda completa
  • `/search <consulta>` - Busca en tu código antes de modificar
  • `/index` - Indexa el proyecto en memoria vectorial
  • `/memory` - Muestra estadísticas de memoria
  • `/new` - Inicia una nueva conversación sin historial
  • `/clear` - Limpia el historial de conversación
  • `/stats` - Muestra estadísticas de la sesión
  • `/exit` o `/quit` - Salir del agente

**Mencionar archivos específicos:**
  • Escribe `@` seguido del nombre del archivo para incluirlo en tu consulta
  • Ejemplo: `@main.py fix the bug in this file`
  • Los archivos mencionados con @ tienen alta prioridad en el contexto

Simplemente describe lo que necesitas y el agente creará un plan y lo ejecutará.
        """
        self.console.print(Panel(Markdown(welcome), title="Información", border_style="green"))
        self.console.print()

    def _initialize_file_indexer(self):
        """Initialize file indexer lazily"""
        if self.file_indexer is None:
            self.file_indexer = FileIndexer(".")
            self.console.print("[dim]📁 Indexing files...[/dim]")
            self.file_indexer.index_directory()
            self.console.print(f"[dim]✓ Indexed {self.file_indexer.get_file_count()} files[/dim]")

    async def get_user_input(self, prompt: str = "") -> str:
        """
        Obtiene input del usuario de manera asíncrona
        Detecta @ para selección de archivos

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
            user_input = user_input.strip()

            # Check for @ mentions
            if '@' in user_input:
                user_input = await self._process_file_mentions(user_input)

            return user_input
        except (EOFError, KeyboardInterrupt):
            return "/exit"

    async def _process_file_mentions(self, user_input: str) -> str:
        """
        Process @ mentions in user input to select files

        Args:
            user_input: User input text

        Returns:
            Processed input with file paths
        """
        # Initialize indexer if needed
        self._initialize_file_indexer()

        # Find all @ mentions
        parts = []
        current_pos = 0

        while True:
            at_pos = user_input.find('@', current_pos)
            if at_pos == -1:
                # No more @ symbols
                parts.append(user_input[current_pos:])
                break

            # Add text before @
            parts.append(user_input[current_pos:at_pos])

            # Extract query after @ (until space or end)
            query_start = at_pos + 1
            query_end = query_start
            while query_end < len(user_input) and user_input[query_end] not in (' ', '\t', '\n'):
                query_end += 1

            query = user_input[query_start:query_end]

            # Show file selector
            self.console.print(f"\n[cyan]Detected @ mention, opening file selector...[/cyan]")

            # Run file selector (synchronously since we're in a coroutine)
            loop = asyncio.get_event_loop()
            selected_file = await loop.run_in_executor(
                None,
                select_file_interactive,
                ".",
                query
            )

            if selected_file:
                # Add selected file to mentioned files list
                if selected_file not in self.mentioned_files:
                    self.mentioned_files.append(selected_file)

                # Replace @ with file path
                parts.append(f"`{selected_file}`")
                self.console.print(f"[green]✓ Selected: {selected_file}[/green]")
            else:
                # User cancelled, keep original @query
                parts.append(f"@{query}")
                self.console.print(f"[yellow]✗ Selection cancelled[/yellow]")

            current_pos = query_end

        result = ''.join(parts)

        # If result is just file mentions with no actual query, ask user to continue
        if result.strip() and all(part.strip().startswith('`') and part.strip().endswith('`') or part.strip() == '' for part in result.split()):
            self.console.print("\n[cyan]💬 Now type your request (you can use @ for more files):[/cyan]")
            # Get additional input from user
            loop = asyncio.get_event_loop()
            additional_input = await loop.run_in_executor(
                None,
                lambda: self.session.prompt("   ")
            )

            # Process the additional input for more @ mentions
            if '@' in additional_input:
                additional_input = await self._process_file_mentions(additional_input)

            result = result + " " + additional_input.strip()

        return result

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

    def start_thinking(self, message: Optional[str] = None):
        """
        Start the vibe spinner to show agent is thinking

        Args:
            message: Optional custom message (uses rotating vibes if None)
        """
        # Stop any existing spinner first
        self.stop_thinking()

        if message:
            # Single custom message
            self.vibe_spinner = VibeSpinner(
                messages=[message],
                spinner_style="dots",
                color="cyan",
                language="es"
            )
        else:
            # Rotating vibe messages
            self.vibe_spinner = VibeSpinner(
                spinner_style="dots",
                color="cyan",
                language="es"
            )

        self.vibe_spinner.start()

    def stop_thinking(self, clear: bool = True):
        """
        Stop the vibe spinner

        Args:
            clear: Whether to clear the spinner line
        """
        if self.vibe_spinner and self.vibe_spinner.is_running():
            self.vibe_spinner.stop(clear_line=clear)
            self.vibe_spinner = None

    def print_thinking(self, message: str = "Pensando..."):
        """
        Muestra un indicador de que el agente está pensando
        (Legacy method - consider using start_thinking/stop_thinking instead)
        """
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

    def print_diff(self, diff_text: str):
        """
        Muestra un diff con colores: rojo para eliminaciones, verde para adiciones

        Args:
            diff_text: Texto del diff en formato unified diff
        """
        self.console.print()
        for line in diff_text.split('\n'):
            if line.startswith('---') or line.startswith('+++'):
                # File headers in cyan
                self.console.print(f"[bold cyan]{line}[/bold cyan]")
            elif line.startswith('@@'):
                # Line numbers in yellow
                self.console.print(f"[bold yellow]{line}[/bold yellow]")
            elif line.startswith('-') and not line.startswith('---'):
                # Deleted lines in red
                self.console.print(f"[bold red]{line}[/bold red]")
            elif line.startswith('+') and not line.startswith('+++'):
                # Added lines in green
                self.console.print(f"[bold green]{line}[/bold green]")
            else:
                # Context lines in dim white
                self.console.print(f"[dim]{line}[/dim]")
        self.console.print()

    def print_task_summary(self, summary: str):
        """
        Muestra el resumen de tarea completada en un formato especial

        Args:
            summary: Texto del resumen generado por el agente
        """
        self.console.print()
        self.console.print("─" * 60, style="dim cyan")
        self.console.print()

        # Render as markdown for nice formatting
        md = Markdown(summary)
        self.console.print(md)

        self.console.print()
        self.console.print("─" * 60, style="dim cyan")
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
• `/search <consulta>` - Busca y analiza código antes de modificarlo

**Memoria y Estado:**
• `/index` - Indexa el proyecto en memoria vectorial (ChromaDB)
• `/memory` - Muestra estadísticas de memoria vectorial
• `/save-state [session]` - Guarda estado completo de agentes (AutoGen)
• `/load-state [session]` - Carga estado de agentes desde sesión
• `/list-sessions` - Lista todas las sesiones guardadas

**Conversación:**
• `/new` - Inicia una nueva conversación sin historial
• `/clear` - Limpia el historial de conversación
• `/stats` - Muestra estadísticas de la sesión
• `/save <archivo>` - Guarda el historial en un archivo (legacy)
• `/load <archivo>` - Carga un historial desde un archivo (legacy)

**Sistema:**
• `/debug` - Activa/desactiva el modo debug
• `/logs` - Muestra la ubicación del archivo de logs
• `/exit` o `/quit` - Salir del agente

**Mencionar Archivos Específicos:**

• Escribe `@` seguido del nombre del archivo para incluirlo con alta prioridad
• Usa las flechas ↑↓ para navegar por los archivos
• Escribe para filtrar archivos en tiempo real
• Presiona Enter para seleccionar, Esc para cancelar

**Ejemplos con @:**

`@main.py fix the authentication bug in this file`

`@src/config/settings.py @.env update the API configuration`

`explain how @src/agents/code_searcher.py works`

**Uso:**

Simplemente escribe lo que necesitas que el agente haga. El agente:
1. Creará un plan de ejecución con tareas
2. Ejecutará cada tarea llamando al agente de código
3. Ajustará el plan si encuentra errores o nueva información
4. Continuará hasta completar el objetivo

**Ejemplos de tareas:**

"Crea una API REST con FastAPI que tenga endpoints para usuarios"

"Encuentra todos los archivos Python con bugs y corrígelos"

"Refactoriza el código en src/utils para usar async/await"

**Ejemplos de búsqueda:**

"/search función de autenticación"

"/search dónde se usa la clase User"

"/search métodos que modifican la base de datos"
        """
        self.print_info(help_text, "Ayuda")

    def print_goodbye(self):
        """Muestra el mensaje de despedida"""
        goodbye = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              Gracias por usar Dave Agent                    ║
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

    def get_mentioned_files(self) -> List[str]:
        """
        Get list of files mentioned with @

        Returns:
            List of mentioned file paths
        """
        return self.mentioned_files.copy()

    def clear_mentioned_files(self):
        """Clear the list of mentioned files"""
        self.mentioned_files.clear()

    def print_mentioned_files(self):
        """Display the list of mentioned files"""
        if not self.mentioned_files:
            return

        self.console.print()
        self.console.print("[bold cyan]📎 Mentioned Files:[/bold cyan]")
        for file_path in self.mentioned_files:
            self.console.print(f"  • [green]{file_path}[/green]")
        self.console.print()

    def get_mentioned_files_content(self) -> str:
        """
        Read content of all mentioned files

        Returns:
            Combined content of all mentioned files with headers
        """
        if not self.mentioned_files:
            return ""

        content_parts = []
        content_parts.append("📎 MENTIONED FILES CONTEXT (High Priority):\n")

        for file_path in self.mentioned_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                content_parts.append(f"\n{'='*60}")
                content_parts.append(f"FILE: {file_path}")
                content_parts.append(f"{'='*60}\n")
                content_parts.append(file_content)
                content_parts.append(f"\n{'='*60}\n")

            except Exception as e:
                content_parts.append(f"\n⚠️ Error reading {file_path}: {e}\n")

        return '\n'.join(content_parts)
