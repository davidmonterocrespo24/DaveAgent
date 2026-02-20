"""
Interactive CLI interface in the style of Claude Code
"""

import asyncio
import functools
import os
import random
import signal
import sys
import time
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.completion import Completer, Completion, WordCompleter, merge_completers
from prompt_toolkit.document import Document
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from src.utils import FileIndexer, VibeSpinner, select_file_interactive

# Platform-specific imports
try:
    import termios
    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False  # Windows doesn't have termios


class FileCompleter(Completer):
    """Custom completer for file paths after @ symbol with fuzzy matching."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self._file_cache = []
        self._cache_time = 0
        self._cache_ttl = 5  # Refresh cache every 5 seconds

    def _refresh_cache(self):
        """Refresh the file cache if TTL expired."""
        current_time = time.time()
        if current_time - self._cache_time > self._cache_ttl:
            self._file_cache = []
            try:
                # Get all files recursively, excluding common directories
                for path in self.base_dir.rglob("*"):
                    if path.is_file():
                        # Skip common excluded directories
                        parts = path.parts
                        if any(excluded in parts for excluded in [
                            '.git', 'node_modules', '__pycache__', '.venv',
                            'venv', '.pytest_cache', '.mypy_cache', 'dist', 'build'
                        ]):
                            continue

                        # Store relative path
                        try:
                            rel_path = str(path.relative_to(self.base_dir))
                            self._file_cache.append(rel_path)
                        except ValueError:
                            continue
            except Exception:
                pass

            self._cache_time = current_time

    def get_completions(self, document: Document, complete_event):
        """Generate completions for files after @ symbol."""
        text = document.text_before_cursor

        # Find the last @ symbol
        at_pos = text.rfind('@')
        if at_pos == -1:
            return

        # Extract the query after @
        query = text[at_pos + 1:]

        # Don't complete if there's a space after @ (means they finished the mention)
        if ' ' in query:
            return

        # Refresh cache if needed
        self._refresh_cache()

        # Fuzzy match files
        query_lower = query.lower()
        matches = []

        for file_path in self._file_cache:
            file_lower = file_path.lower()

            # Simple fuzzy matching: all query chars must appear in order
            if self._fuzzy_match(query_lower, file_lower):
                # Calculate score (shorter paths score higher)
                score = len(file_path)
                if file_lower.startswith(query_lower):
                    score -= 1000  # Prefix matches score much higher

                matches.append((score, file_path))

        # Sort by score and yield top 20
        matches.sort(key=lambda x: x[0])
        for _, file_path in matches[:20]:
            # Show completion starting from the query position
            yield Completion(
                file_path,
                start_position=-len(query),
                display=f"📄 {file_path}",
            )

    def _fuzzy_match(self, query: str, text: str) -> bool:
        """Check if all characters in query appear in text in order."""
        if not query:
            return True

        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1

        return query_idx == len(query)


class CLIInterface:
    """Rich and interactive CLI interface for DaveAgent"""

    def __init__(self):
        self.console = Console()
        self._executor = None  # Lazy-initialized thread pool for async rendering

        # Ensure .daveagent directory exists
        history_dir = Path(".daveagent")
        history_dir.mkdir(exist_ok=True)
        history_file = history_dir / ".agent_history"

        # Setup key bindings for bracketed paste mode
        kb = KeyBindings()

        @kb.add(Keys.BracketedPaste)
        def _(event):
            """Handle bracketed paste - insert content without executing"""
            # Get pasted data
            data = event.data
            # Insert into buffer as single block (prevents line-by-line execution)
            event.current_buffer.insert_text(data)

        # Setup command completer (slash commands)
        command_words = [
            '/help', '/exit', '/quit',
            '/agent-mode', '/chat-mode',
            '/new-session', '/load-session', '/save-session', '/list-sessions',
            '/config', '/set-model', '/set-url',
            '/cron', '/cron-list', '/cron-add', '/cron-remove', '/cron-enable',
            '/subagents', '/subagent-status',
            '/index', '/index-status', '/index-rebuild',
            '/memory', '/memory-clear',
            '/stats', '/clear', '/history',
            '/debug', '/debug-on', '/debug-off',
            '/telemetry', '/telemetry-on', '/telemetry-off',
        ]
        command_completer = WordCompleter(
            command_words,
            ignore_case=True,
            sentence=True,  # Allow completion in middle of sentence
        )

        # Setup file completer for @ mentions
        file_completer = FileCompleter(base_dir=".")

        # Merge completers: commands + files
        combined_completer = merge_completers([command_completer, file_completer])

        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=kb,  # Enable bracketed paste mode
            completer=combined_completer,  # Enable command and file completion
            complete_while_typing=True,  # Show completions as you type
            enable_open_in_editor=False,
            multiline=False,  # Enter submits (single line mode)
        )
        self.conversation_active = False
        self.file_indexer = None  # Will be initialized on first use
        self.mentioned_files: list[str] = []  # Track files mentioned with @
        self.vibe_spinner: VibeSpinner | None = None  # Spinner for thinking animation
        self.current_mode = "agent"  # Track current mode for display

        # Terminal state management (Nanobot-style)
        self._saved_term_attrs = None
        self._save_terminal_state()

        # Setup signal handlers for graceful cleanup
        signal.signal(signal.SIGINT, self._handle_interrupt)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._handle_terminate)

    # =========================================================================
    # TERMINAL STATE MANAGEMENT (Nanobot-style)
    # =========================================================================

    def _save_terminal_state(self):
        """Save terminal attributes for later recovery."""
        if not TERMIOS_AVAILABLE:
            return  # Skip on Windows

        try:
            if os.isatty(sys.stdin.fileno()):
                self._saved_term_attrs = termios.tcgetattr(sys.stdin.fileno())
        except Exception:
            # Silently fail if we can't save terminal state
            pass

    def _restore_terminal_state(self):
        """Restore terminal to original state."""
        if not TERMIOS_AVAILABLE or not self._saved_term_attrs:
            return

        try:
            termios.tcsetattr(
                sys.stdin.fileno(),
                termios.TCSADRAIN,
                self._saved_term_attrs
            )
        except Exception:
            pass

    def _flush_pending_tty_input(self):
        """
        Drop unread keypresses typed while model was generating.

        This prevents "ghost characters" from appearing after long outputs.
        Inspired by Nanobot's implementation.
        """
        if not TERMIOS_AVAILABLE:
            return  # Skip on Windows

        try:
            fd = sys.stdin.fileno()
            if not os.isatty(fd):
                return

            # Flush input buffer
            termios.tcflush(fd, termios.TCIFLUSH)
        except Exception:
            pass

    def _handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        self._restore_terminal_state()
        self.console.print("\n\n[yellow]👋 Interrupted by user[/yellow]")
        sys.exit(0)

    def _handle_terminate(self, signum, frame):
        """Handle termination signal."""
        self._restore_terminal_state()
        sys.exit(0)

    def __del__(self):
        """Cleanup on destruction."""
        self._restore_terminal_state()
        # Cleanup executor if initialized
        if self._executor:
            self._executor.shutdown(wait=False)

    async def _run_in_executor(self, func, *args):
        """
        Run a synchronous function in a thread pool to prevent blocking the event loop.

        This is critical for heavy rendering operations (Rich panels, syntax highlighting)
        that can block for seconds on large files.
        """
        if self._executor is None:
            import concurrent.futures
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, func, *args)

    # =========================================================================
    # CLI INTERFACE METHODS
    # =========================================================================

    def print_banner(self):
        """Shows the welcome banner with a 'particles' animation"""

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
║              Intelligent Development Agent                   ║
║                    Version 1.2.1                             ║
╚══════════════════════════════════════════════════════════════╝
        """.strip("\n").split("\n")

        height = len(banner_lines)
        width = max(len(line) for line in banner_lines)

        # Characters to use as "particles"
        particles = [".", ":", "*", "°", "·", " "]

        # 1. Create initial state (particle field)
        # Use a list of character lists so we can mutate it
        current_state = []
        for r in range(height):
            row = []
            for c in range(width):
                # If there's a character in the final banner, place a particle
                if c < len(banner_lines[r]) and banner_lines[r][c] != " ":
                    row.append(random.choice(particles))
                else:
                    row.append(" ")  # Keep empty spaces
            current_state.append(row)

        # 2. Get all coordinates (row, col) of the real characters
        coords = []
        for r in range(height):
            for c in range(width):
                # We only want to "resolve" characters that are not spaces
                if c < len(banner_lines[r]) and banner_lines[r][c] != " ":
                    coords.append((r, c))

        # 3. Shuffle coordinates for random assembly effect
        random.shuffle(coords)

        # 4. Set up animation with Rich Live
        # Define how many characters to reveal per frame (lower = slower)
        reveal_per_frame = max(1, len(coords) // 20)  # Aim for ~20 frames

        with Live(console=self.console, refresh_per_second=15, transient=True) as live:
            # Show initial particle field for a moment
            text = Text("\n".join("".join(row) for row in current_state), style="bold cyan")
            live.update(text)
            time.sleep(0.3)  # Initial pause

            # 5. Start revealing characters in batches
            for i in range(0, len(coords), reveal_per_frame):
                batch = coords[i : i + reveal_per_frame]

                for r, c in batch:
                    # Replace particle with correct character
                    current_state[r][c] = banner_lines[r][c]

                # Update Live with new state
                text = Text("\n".join("".join(row) for row in current_state), style="bold cyan")
                live.update(text)
                time.sleep(0.02)  # Small pause between frames

        # 6. Print final banner permanently
        # (Live with transient=True disappears, so we print it again)
        final_text = Text("\n".join(banner_lines), style="bold cyan")
        self.console.print(final_text)
        self.console.print()

    def _initialize_file_indexer(self):
        """Initialize file indexer lazily"""
        if self.file_indexer is None:
            self.file_indexer = FileIndexer(".")
            self.console.print("[dim]📁 Indexing files...[/dim]")
            self.file_indexer.index_directory()
            self.console.print(f"[dim]✓ Indexed {self.file_indexer.get_file_count()} files[/dim]")

    def set_mode(self, mode: str):
        """
        Updates the current mode for display

        Args:
            mode: "agent" or "chat"
        """
        self.current_mode = mode

    async def get_user_input(self, prompt: str = "") -> str:
        """
        Gets user input asynchronously with HTML formatted prompt.
        Detects @ for file selection.
        Uses patch_stdout to prevent output conflicts.

        Args:
            prompt: Prompt text (plain string or HTML)

        Returns:
            User input
        """
        # Flush any pending TTY input before prompting
        self._flush_pending_tty_input()

        if not prompt:
            # Create HTML formatted prompt with mode indicator (Nanobot-style)
            mode_indicator = "🔧" if self.current_mode == "agent" else "💬"
            mode_text = self.current_mode.upper()
            prompt = HTML(f"<b fg='ansibrightcyan'>[{mode_indicator} {mode_text}]</b> <b fg='ansiyellow'>You:</b> ")
        elif isinstance(prompt, str):
            # Convert plain string to HTML if needed
            prompt = HTML(f"<ansiyellow>{prompt}</ansiyellow>")

        try:
            # Use patch_stdout to prevent conflicts with Rich output
            with patch_stdout():
                # Ejecutar el prompt en un executor para no bloquear el loop
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, lambda: self.session.prompt(prompt))
                user_input = user_input.strip()

            # Check for @ mentions
            if "@" in user_input:
                user_input = await self._process_file_mentions(user_input)

            return user_input
        except (EOFError, KeyboardInterrupt):
            # Restore terminal state on interrupt
            self._restore_terminal_state()
            return "/exit"
        except Exception as e:
            # Restore terminal state on any error
            self._restore_terminal_state()
            self.console.print(f"[red]Error getting input: {e}[/red]")
            return ""

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
            at_pos = user_input.find("@", current_pos)
            if at_pos == -1:
                # No more @ symbols
                parts.append(user_input[current_pos:])
                break

            # Add text before @
            parts.append(user_input[current_pos:at_pos])

            # Extract query after @ (until space or end)
            query_start = at_pos + 1
            query_end = query_start
            while query_end < len(user_input) and user_input[query_end] not in (" ", "\t", "\n"):
                query_end += 1

            query = user_input[query_start:query_end]

            # Show file selector
            self.console.print("\n[cyan]Detected @ mention, opening file selector...[/cyan]")

            # Run file selector (synchronously since we're in a coroutine)
            loop = asyncio.get_event_loop()
            selected_file = await loop.run_in_executor(None, select_file_interactive, ".", query)

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
                self.console.print("[yellow]✗ Selection cancelled[/yellow]")

            current_pos = query_end

        result = "".join(parts)

        # If result is just file mentions with no actual query, ask user to continue
        if result.strip() and all(
            part.strip().startswith("`") and part.strip().endswith("`") or part.strip() == ""
            for part in result.split()
        ):
            self.console.print(
                "\n[cyan]💬 Now type your request (you can use @ for more files):[/cyan]"
            )
            # Get additional input from user
            loop = asyncio.get_event_loop()
            additional_input = await loop.run_in_executor(None, lambda: self.session.prompt("   "))

            # Process the additional input for more @ mentions
            if "@" in additional_input:
                additional_input = await self._process_file_mentions(additional_input)

            result = result + " " + additional_input.strip()

        return result

    def print_user_message(self, message: str):
        """Shows a user message"""
        self.console.print()
        self.console.print(f"[bold blue]You:[/bold blue] {message}")
        self.console.print()

    def print_agent_message(self, message: str, agent_name: str = "Agent"):
        """Shows an agent message"""
        self.console.print(f"[bold green]{agent_name}:[/bold green]")
        self.console.print(Panel(Markdown(message), border_style="green"))
        self.console.print()

    def print_plan(self, plan_summary: str):
        """Shows the execution plan"""
        self.console.print()
        self.console.print(
            Panel(plan_summary, title="[bold cyan]Execution Plan[/bold cyan]", border_style="cyan")
        )
        self.console.print()

    def print_task_start(self, task_id: int, task_title: str, task_description: str):
        """Shows that a task is starting"""
        self.console.print()
        self.console.print(
            f"[bold yellow]⚡ Executing Task {task_id}:[/bold yellow] {task_title}", style="bold"
        )
        self.console.print(f"   {task_description}", style="dim")
        self.console.print()

    def print_task_complete(self, task_id: int, task_title: str, result_summary: str):
        """Shows that a task was completed"""
        self.console.print()
        self.console.print(f"[bold green]✓ Task {task_id} Completed:[/bold green] {task_title}")
        if result_summary:
            self.console.print(Panel(result_summary, border_style="green", title="Result"))
        self.console.print()

    def print_task_failed(self, task_id: int, task_title: str, error: str):
        """Shows that a task failed"""
        self.console.print()
        self.console.print(f"[bold red]✗ Task {task_id} Failed:[/bold red] {task_title}")
        self.console.print(Panel(error, border_style="red", title="Error"))
        self.console.print()

    def print_plan_update(self, reasoning: str, changes_summary: str):
        """Shows that the plan is being updated"""
        self.console.print()
        self.console.print("[bold yellow]🔄 Updating Execution Plan[/bold yellow]")
        self.console.print(
            Panel(
                f"**Reasoning:**\n{reasoning}\n\n**Changes:**\n{changes_summary}",
                border_style="yellow",
            )
        )
        self.console.print()

    def start_thinking(self, message: str | None = None):
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
                messages=[message], spinner_style="dots", color="cyan", language="es"
            )
        else:
            # Rotating vibe messages
            self.vibe_spinner = VibeSpinner(spinner_style="dots", color="cyan", language="es")

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

    def print_thinking(self, message: str = "Thinking..."):
        """
        Shows an indicator that the agent is thinking
        (Legacy method - consider using start_thinking/stop_thinking instead)
        """
        self.console.print(f"[dim]{message}[/dim]")

    def print_error(self, error: str):
        """Shows an error message"""
        self.console.print(Panel(error, title="[bold red]Error[/bold red]", border_style="red"))

    def print_warning(self, warning: str):
        """Shows a warning message"""
        self.console.print(
            Panel(warning, title="[bold yellow]Warning[/bold yellow]", border_style="yellow")
        )

    def print_info(self, info: str, title: str = "Information"):
        """Shows an informative message"""
        self.console.print(
            Panel(info, title=f"[bold cyan]{title}[/bold cyan]", border_style="cyan")
        )

    def print_success(self, message: str):
        """Shows a success message"""
        self.console.print(f"[bold green]✓ {message}[/bold green]")

    def print_diff(self, diff_text: str):
        """
        Shows a diff with colors: red for deletions, green for additions

        Args:
            diff_text: Diff text in unified diff format
        """
        for line in diff_text.split("\n"):
            if line.startswith("---") or line.startswith("+++"):
                # File headers in cyan
                self.console.print(f"[bold cyan]{line}[/bold cyan]")
            elif line.startswith("@@"):
                # Line numbers in yellow
                self.console.print(f"[bold yellow]{line}[/bold yellow]")
            elif line.startswith("-") and not line.startswith("---"):
                # Deleted lines in red
                self.console.print(f"[bold red]{line}[/bold red]")
            elif line.startswith("+") and not line.startswith("+++"):
                # Added lines in green
                self.console.print(f"[bold green]{line}[/bold green]")
            else:
                # Context lines in dim white
                self.console.print(f"[dim]{line}[/dim]")

    def _print_code_sync(self, code: str, filename: str, max_lines: int = 50):
        """
        Internal synchronous version of print_code for executor.

        DO NOT call directly - use print_code() instead.
        """
        # Map file extensions to language names for syntax highlighting
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sql": "sql",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "zsh",
            ".ps1": "powershell",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".lua": "lua",
            ".pl": "perl",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "ini",
            ".dockerfile": "dockerfile",
            ".tf": "terraform",
            ".vue": "vue",
            ".svelte": "svelte",
        }

        # Get file extension and determine language
        ext = Path(filename).suffix.lower()
        language = extension_map.get(ext, "text")

        # Truncate if too long
        lines = code.split("\n")
        truncated = False
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True
            code = "\n".join(lines)

        try:
            syntax = Syntax(
                code,
                language,
                theme="monokai",
                line_numbers=True,
                word_wrap=False,
            )
            self.console.print(
                Panel(
                    syntax,
                    title=f"[bold cyan]{filename}[/bold cyan]",
                    border_style="dim",
                    subtitle=f"[dim]{language}[/dim]" if language != "text" else None,
                )
            )
            if truncated:
                self.console.print(
                    f"[dim]... (showing first {max_lines} lines, file has {len(lines) + (len(code.split(chr(10))) - max_lines)} total)[/dim]"
                )
        except Exception:
            # Fallback to plain text if syntax highlighting fails
            self.console.print(
                Panel(code, title=f"[bold cyan]{filename}[/bold cyan]", border_style="dim")
            )

    async def print_code(self, code: str, filename: str, max_lines: int = 50):
        """
        Display code with syntax highlighting (async, non-blocking version).

        Args:
            code: The code content to display
            filename: The filename (used to determine language)
            max_lines: Maximum lines to display (truncates if longer)
        """
        # Run heavy rendering in executor to prevent blocking
        await self._run_in_executor(self._print_code_sync, code, filename, max_lines)

    def print_task_summary(self, summary: str):
        """
        Shows the completed task summary in a special format

        Args:
            summary: Summary text generated by the agent
        """
        self.console.print("─" * 60, style="dim cyan")
        # Render as markdown for nice formatting
        md = Markdown(summary)
        self.console.print(md)
        self.console.print("─" * 60, style="dim cyan")

    def create_progress_table(self, tasks: list[dict]) -> Table:
        """Creates a table with task progress"""
        table = Table(title="Task Progress", show_header=True, header_style="bold")
        table.add_column("ID", style="cyan", width=4)
        table.add_column("Status", width=12)
        table.add_column("Task", style="white")

        status_styles = {
            "completed": "[green]✓ Completed[/green]",
            "in_progress": "[yellow]⚡ In progress[/yellow]",
            "pending": "[dim]○ Pending[/dim]",
            "failed": "[red]✗ Failed[/red]",
            "blocked": "[red]⊟ Blocked[/red]",
        }

        for task in tasks:
            table.add_row(
                str(task["id"]), status_styles.get(task["status"], task["status"]), task["title"]
            )

        return table

    def print_statistics(self, stats: dict):
        """Shows session statistics"""
        stats_text = f"""
**Current Session Statistics:**

• Total messages: {stats.get("total_messages", 0)}
• First message: {stats.get("first_message", "N/A")}
• Last message: {stats.get("last_message", "N/A")}

**Note:** To see the complete agent state, use `/list-sessions`
**Persistence:** State is automatically saved using AutoGen save_state()
        """
        self.console.print()
        self.console.print(
            Panel(
                Markdown(stats_text), title="[bold cyan]Statistics[/bold cyan]", border_style="cyan"
            )
        )
        self.console.print()

    def print_help(self):
        """Shows the help"""
        help_text = """
**Available Commands:**

• `/help` - Shows this help message

**Model Configuration:**
• `/config` - Shows current configuration (model, URL, API key)
• `/set-model <model>` - Change LLM model (e.g.: deepseek-chat, deepseek-reasoner, gpt-4)
• `/set-url <url>` - Change provider base URL (e.g.: https://api.deepseek.com)

**Note:** You can also configure the model in `.daveagent/.env`:
```
DAVEAGENT_API_KEY=tu-api-key
DAVEAGENT_BASE_URL=https://api.deepseek.com
DAVEAGENT_MODEL=deepseek-reasoner
```

**Operation Modes:**
• `/agent-mode` - Activate AGENT mode (with modification tools)
• `/chat-mode` - Activate CHAT mode (read-only, no file modifications)

**Session Management:**
• `/new-session <title>` - Create new session with metadata
• `/save-session [title]` - Save current session (with optional title)
• `/load-session [id]` - Load saved session (most recent if not specified)
• `/sessions` - List all sessions with Rich table
• `/history` - Show current session history
• `/history --all` - Show complete history (no limit)
• `/history --thoughts` - Include agent reasoning

**Memory and State:**
• `/index` - Index project in vector memory (ChromaDB)
• `/memory` - Show vector memory statistics
• `/save-state` - Alias for /save-session
• `/load-state` - Alias for /load-session

**Conversation:**
• `/new` - Start a new conversation without history
• `/clear` - Clear conversation history in memory
• `/stats` - Show current session statistics

**System:**
• `/init` - Create a DAVEAGENT.md template for project-specific context
• `/telemetry` - Show telemetry status
• `/telemetry-off` - Disable telemetry (anonymous usage data)
• `/telemetry-on` - Enable telemetry
• `/debug` - Toggle debug mode
• `/logs` - Show log file location
• `/exit` or `/quit` - Exit the agent

**Subagents (Parallel Execution):**
• `/subagents` - List all active subagents
• `/subagent-status <id>` - Show detailed status of a specific subagent

**Cron (Scheduled Tasks):**
• `/cron list` - List all scheduled jobs
• `/cron add at <time> <task>` - Schedule one-time task (e.g., 2026-02-20T15:30)
• `/cron add every <interval> <task>` - Schedule recurring task (e.g., 1h, 30m, 2d)
• `/cron add cron '<expr>' <task>` - Schedule with cron expression (e.g., '0 9 * * *')
• `/cron enable <id>` - Enable a disabled job
• `/cron disable <id>` - Disable a job temporarily
• `/cron remove <id>` - Delete a job permanently
• `/cron run <id>` - Manually trigger a job now

**Mention Specific Files:**

• Write `@` followed by the file name to include it with high priority
• Use arrow keys ↑↓ to navigate through files
• Type to filter files in real-time
• Press Enter to select, Esc to cancel

**Examples with @:**

`@main.py fix the authentication bug in this file`

`@src/config/settings.py @.env update the API configuration`

`explain how @src/main.py works`

**Operation Modes (NEW):**

**AGENT Mode (default):**
- All tools enabled (read + modification)
- Can modify files, run commands, make commits, etc.
- Uses routing system (simple/complex)
- Ideal for active development and code modifications

**CHAT Mode:**
- Only read tools enabled
- Can read files, search code, analyze, query APIs
- CANNOT modify files or run commands
- Ideal for queries, analysis, and risk-free learning

To change modes:
- `/agent-mode` - Enable all tools
- `/chat-mode` - Disable modification tools

**Workflow with Sessions:**

1. **Create new session:** `/new-session "My API Project"`
2. **Work normally:** State is saved automatically
3. **Save manually:** `/save-session` (updates current session)
4. **List sessions:** `/sessions` to see all saved sessions
5. **Load session:** `/load-session 20250105_143000` restores complete context
6. **View history:** `/history` shows formatted complete conversation

**State Persistence:**

The system uses **AutoGen save_state/load_state** to save the complete context:
- Automatically saved every 5 minutes
- Saved when closing the application
- Includes all conversation history from all agents
- Sessions include metadata: title, tags, description, timestamps

**Usage:**

Simply write what you need the agent to do. The agent will:
1. Create an execution plan with tasks
2. Execute each task by calling the code agent
3. Adjust the plan if it encounters errors or new information
4. Continue until the objective is completed

**Task Examples:**

"Create a REST API with FastAPI that has endpoints for users"

"Find all Python files with bugs and fix them"

"Refactor the code in src/utils to use async/await"
        """
        self.console.print()
        self.console.print(
            Panel(Markdown(help_text), title="[bold cyan]Help[/bold cyan]", border_style="cyan")
        )
        self.console.print()

    def print_goodbye(self):
        """Shows the goodbye message"""
        goodbye = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              Thank you for using Dave Agent                  ║
║                   See you soon!                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        self.console.print()
        self.console.print(goodbye, style="bold cyan")
        self.console.print()

    def clear_screen(self):
        """Clears the screen"""
        self.console.clear()

    def get_mentioned_files(self) -> list[str]:
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
                with open(file_path, encoding="utf-8") as f:
                    file_content = f.read()

                content_parts.append(f"\n{'=' * 60}")
                content_parts.append(f"FILE: {file_path}")
                content_parts.append(f"{'=' * 60}\n")
                content_parts.append(file_content)
                content_parts.append(f"\n{'=' * 60}\n")

            except Exception as e:
                content_parts.append(f"\n⚠️ Error reading {file_path}: {e}\n")

        return "\n".join(content_parts)

    # =========================================================================
    # SUBAGENT VISUALIZATION (Enhanced Terminal Integration)
    # =========================================================================

    def print_subagent_spawned(self, subagent_id: str, label: str, task: str):
        """Show enhanced subagent spawn notification.

        Args:
            subagent_id: Unique ID of the subagent
            label: Human-readable label
            task: Task description
        """
        self.console.print(
            Panel(
                f"[cyan]Task:[/cyan] {task}\n\n"
                f"[dim]Subagent ID: {subagent_id}[/dim]\n"
                f"[dim]This task will run in the background. You'll be notified when it completes.[/dim]",
                title=f"[bold green]🚀 Subagent Spawned: {label}[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
        )

    def print_subagent_progress(self, subagent_id: str, label: str, progress_msg: str):
        """Show subagent progress update.

        Args:
            subagent_id: Unique ID of the subagent
            label: Human-readable label
            progress_msg: Progress message
        """
        self.console.print(
            f"[dim]🔄 Subagent '{label}' ({subagent_id[:8]}): {progress_msg}[/dim]"
        )

    def print_subagent_completed(self, subagent_id: str, label: str, summary: str):
        """Show enhanced subagent completion notification.

        Args:
            subagent_id: Unique ID of the subagent
            label: Human-readable label
            summary: Brief summary of results
        """
        self.console.print(
            Panel(
                f"[green]{summary}[/green]\n\n"
                f"[dim]Subagent ID: {subagent_id}[/dim]\n"
                f"[dim]The results are being processed by the agent...[/dim]",
                title=f"[bold green]✓ Subagent Completed: {label}[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
        )

    def print_subagent_failed(self, subagent_id: str, label: str, error: str):
        """Show enhanced subagent failure notification.

        Args:
            subagent_id: Unique ID of the subagent
            label: Human-readable label
            error: Error message
        """
        self.console.print(
            Panel(
                f"[red]{error}[/red]\n\n"
                f"[dim]Subagent ID: {subagent_id}[/dim]\n"
                f"[dim]The agent will handle this failure and suggest alternatives.[/dim]",
                title=f"[bold red]✗ Subagent Failed: {label}[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
        )

    def print_background_notification(self, title: str, message: str, style: str = "cyan"):
        """Show a background notification (non-intrusive).

        Args:
            title: Notification title
            message: Notification message
            style: Color style (cyan, green, yellow, red)
        """
        self.console.print(f"[dim][{style}]💬 {title}:[/{style}] {message}[/dim]")
