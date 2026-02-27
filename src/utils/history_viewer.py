"""
History Viewer - Rich visualization of conversation history

Displays session history in a formatted and user-friendly way
using Rich for tables, panels, and syntax highlighting.
"""

from datetime import datetime
from typing import Any

from rich import box
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


class HistoryViewer:
    """Conversation history viewer with Rich"""

    def __init__(self, console=None):
        """
        Initialize HistoryViewer

        Args:
            console: Rich Console instance (creates new WindowsSafeConsole if None)
        """
        if console is None:
            from src.utils.vibe_spinner import WindowsSafeConsole
            console = WindowsSafeConsole()
        self.console = console

    def display_sessions_list(self, sessions: list[dict[str, Any]]):
        """
        Display list of sessions in a table

        Args:
            sessions: List of session metadata dicts
        """
        if not sessions:
            self.console.print("\n[yellow]📭 No saved sessions[/yellow]\n")
            return

        # Create table
        table = Table(
            title="📋 Saved Sessions", box=box.ROUNDED, show_header=True, header_style="bold cyan"
        )

        table.add_column("#", style="dim", width=4)
        table.add_column("Title", style="bold")
        table.add_column("ID", style="dim")
        table.add_column("Messages", justify="right", style="green")
        table.add_column("Last interaction", style="yellow")
        table.add_column("Tags", style="magenta")

        # Add rows
        for i, session in enumerate(sessions, 1):
            session_id = session.get("session_id", "unknown")
            title = session.get("title", "Untitled")
            total_messages = session.get("total_messages", 0)
            last_interaction = session.get("last_interaction", "")
            tags = ", ".join(session.get("tags", []))

            # Format date
            if last_interaction:
                try:
                    dt = datetime.fromisoformat(last_interaction)
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    formatted_date = last_interaction

            table.add_row(
                str(i),
                title,
                session_id[:16] + "..." if len(session_id) > 16 else session_id,
                str(total_messages),
                formatted_date,
                tags or "-",
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def display_session_metadata(self, metadata: dict[str, Any], session_id: str):
        """
        Display session metadata in a panel

        Args:
            metadata: Session metadata dict
            session_id: Session ID
        """
        # Create metadata table
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column("Field", style="cyan")
        info_table.add_column("Value", style="white")

        # Add metadata fields
        info_table.add_row("Session ID", session_id)
        info_table.add_row("Title", metadata.get("title", "Untitled"))

        if metadata.get("description"):
            info_table.add_row("Description", metadata.get("description"))

        tags = metadata.get("tags")
        if tags:
            tags_str = ", ".join(tags)
            info_table.add_row("Tags", tags_str)

        created_at = metadata.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at)
                formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
                info_table.add_row("Created", formatted)
            except Exception:
                info_table.add_row("Created", created_at)

        last_interaction = metadata.get("last_interaction", "")
        if last_interaction:
            try:
                dt = datetime.fromisoformat(last_interaction)
                formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
                info_table.add_row("Last interaction", formatted)
            except Exception:
                info_table.add_row("Last interaction", last_interaction)

        # Display in panel
        panel = Panel(
            info_table, title="📊 Session Information", border_style="cyan", box=box.ROUNDED
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print("\n")

    def display_conversation_history(
        self,
        messages: list[dict[str, Any]],
        max_messages: int | None = None,
        show_thoughts: bool = False,
    ):
        """
        Display conversation history with formatted messages

        Args:
            messages: List of message dicts
            max_messages: Maximum number of messages to show (None = all)
            show_thoughts: Include thought/reasoning messages
        """
        if not messages:
            self.console.print("\n[yellow]💬 No messages in history[/yellow]\n")
            return

        # Limit messages if requested
        if max_messages:
            messages = messages[-max_messages:]

        self.console.print("\n")
        self.console.print(
            Panel(
                f"[bold cyan]📜 Conversation History[/bold cyan]\n"
                f"[dim]Showing {len(messages)} message(s)[/dim]",
                box=box.ROUNDED,
            )
        )
        self.console.print("\n")

        # Display each message
        for i, msg in enumerate(messages, 1):
            self._display_message(msg, i, show_thoughts)

        self.console.print("\n")

    def _display_message(self, msg: dict[str, Any], index: int, show_thoughts: bool):
        """
        Display a single message

        Args:
            msg: Message dict
            index: Message number
            show_thoughts: Show thought content
        """
        source = msg.get("source", "unknown")
        msg_type = msg.get("type", "unknown")
        content = msg.get("content", "")
        thought = msg.get("thought")

        # Determine message style
        if source == "user":
            icon = "👤"
            border_style = "blue"
            title_style = "bold blue"
        else:
            icon = "🤖"
            border_style = "green"
            title_style = "bold green"

        # Create title
        title = f"{icon} {source} (message {index})"

        # Check if content is code
        content_str = str(content)

        # Try to detect code blocks
        if "```" in content_str:
            # Render as markdown
            md = Markdown(content_str)
            panel_content = md
        elif content_str.strip().startswith("def ") or content_str.strip().startswith("class "):
            # Looks like Python code
            syntax = Syntax(content_str, "python", theme="monokai", line_numbers=False)
            panel_content = syntax
        else:
            # Regular text
            panel_content = content_str

        # Create panel
        panel = Panel(
            panel_content,
            title=title,
            title_align="left",
            border_style=border_style,
            box=box.ROUNDED,
        )

        self.console.print(panel)
        self.console.print("")

        # Show thought if present and requested
        if show_thoughts and thought:
            thought_panel = Panel(
                f"[dim italic]{thought}[/dim italic]",
                title="💭 Reasoning",
                title_align="left",
                border_style="yellow",
                box=box.SIMPLE,
            )
            self.console.print(thought_panel)
            self.console.print("")

    def display_session_summary(
        self, session_id: str, metadata: dict[str, Any], total_messages: int, agents_used: list[str]
    ):
        """
        Display comprehensive session summary

        Args:
            session_id: Session ID
            metadata: Session metadata
            total_messages: Total message count
            agents_used: List of agent names that participated
        """
        # Create summary content
        summary_parts = []

        summary_parts.append(f"[bold]Session:[/bold] {session_id}")
        summary_parts.append(f"[bold]Title:[/bold] {metadata.get('title', 'Untitled')}")

        if metadata.get("description"):
            summary_parts.append(f"[bold]Description:[/bold] {metadata.get('description')}")

        summary_parts.append("\n[bold cyan]📊 Statistics:[/bold cyan]")
        summary_parts.append(f"  • Total messages: {total_messages}")
        summary_parts.append(f"  • Participating agents: {len(agents_used)}")

        if agents_used:
            agents_str = ", ".join(agents_used)
            summary_parts.append(f"  • Agents: {agents_str}")

        tags = metadata.get("tags")
        if tags:
            tags_str = ", ".join(tags)
            summary_parts.append(f"\n[bold magenta]🏷️  Tags:[/bold magenta] {tags_str}")

        summary_text = "\n".join(summary_parts)

        # Display in panel
        panel = Panel(summary_text, title="📋 Session Summary", border_style="cyan", box=box.DOUBLE)

        self.console.print("\n")
        self.console.print(panel)
        self.console.print("\n")

    def prompt_session_selection(self, sessions: list[dict[str, Any]]) -> str | None:
        """
        Display sessions and prompt for selection

        Args:
            sessions: List of session metadata dicts

        Returns:
            Selected session ID or None
        """
        if not sessions:
            self.console.print("\n[yellow]No sessions available[/yellow]\n")
            return None

        # Display sessions table
        self.display_sessions_list(sessions)

        # Prompt for selection
        self.console.print("[cyan]Select a session:[/cyan]")
        self.console.print("[dim]  • Enter the session number[/dim]")
        self.console.print("[dim]  • Or enter the complete session_id[/dim]")
        self.console.print("[dim]  • Press Enter to cancel[/dim]\n")

        return None  # Actual input would be handled by CLI

    def display_loading_session(self, session_id: str, title: str):
        """
        Display loading animation for session

        Args:
            session_id: Session ID being loaded
            title: Session title
        """
        self.console.print(f"\n[cyan]📂 Loading session:[/cyan] [bold]{title}[/bold]")
        self.console.print(f"[dim]ID: {session_id}[/dim]\n")

    def display_session_loaded(self, session_id: str, total_messages: int, agents_restored: int):
        """
        Display success message after loading session

        Args:
            session_id: Loaded session ID
            total_messages: Number of messages restored
            agents_restored: Number of agents restored
        """
        self.console.print("\n[green]✅ Session loaded successfully![/green]")
        self.console.print(f"  • Session: {session_id}")
        self.console.print(f"  • Messages restored: {total_messages}")
        self.console.print(f"  • Agents restored: {agents_restored}\n")

    def display_no_sessions(self):
        """Display message when no sessions exist"""
        panel = Panel(
            "[yellow]No saved sessions.[/yellow]\n\n"
            "[dim]Use /new-session to create a new session\n"
            "or start chatting to create an automatic session.[/dim]",
            title="📭 No Sessions",
            border_style="yellow",
            box=box.ROUNDED,
        )
        self.console.print("\n")
        self.console.print(panel)
        self.console.print("\n")
