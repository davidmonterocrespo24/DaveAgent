"""
Interaction utilities for Human-in-the-Loop approval.
"""

import sys

from src.utils.errors import UserCancelledError


async def ask_for_approval(action_description: str, context: str = "") -> str | None:
    """
    Interactively asks the user for approval to execute an action.

    Args:
        action_description: A short summary of the action (e.g., "Execute command...").
        context: Detailed context or code block to display (e.g., the command itself).

    Returns:
        None if approved.
        A string message if cancelled or if feedback is provided.
    """
    import asyncio

    # Check if running in headless mode (subagents/background tasks)
    from src.utils.headless_context import is_headless
    if is_headless():
        # Auto-approve in headless mode (no user interaction)
        return None

    try:
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice
        from rich.console import Console, Group
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.text import Text

        from src.utils.permissions import get_permission_manager

        # Import VibeSpinner and PermissionManager
        from src.utils.vibe_spinner import VibeSpinner

        console = Console()
        perm_mgr = get_permission_manager()

        # 1. Construct Action String for Permissions
        # Normalize to Bash(...), Read(...), or WriteFile(...) based on description.
        # IMPORTANT: never include file contents in the permission key - only identifiers.
        action_string = f"{action_description}({context})"
        if "Run terminal command" in action_description or "Execute command" in action_description:
            action_string = f"Bash({context.strip()})"
        elif "Read file" in action_description:
            action_string = f"Read({context.strip()})"
        elif "WRITE FILE:" in action_description:
            # Extract just the filename from "WRITE FILE: filename"
            filename = action_description.replace("WRITE FILE:", "").strip()
            action_string = f"WriteFile({filename})"

        # 2. Check Persistent Permissions
        perm_status = perm_mgr.check_permission(action_string)
        if perm_status == "allow":
            console.print(f"[dim]Auto-approved by settings: {action_string}[/dim]")
            return None
        elif perm_status == "deny":
            return "Action denied by persistent settings."

        # Pause any active spinner to prevent interference
        # Pause active spinner during user interaction
        active_spinner = VibeSpinner.pause_active_spinner()

        # Clear any potential artifacts visually
        sys.stdout.write("\r" + " " * 120 + "\r")
        sys.stdout.flush()

        try:
            from rich.syntax import Syntax

            warning_text = Text("WARNING: This action requires approval.", style="bold yellow")

            # Detect content type for best rendering
            # Strip markdown code fences if present
            raw_context = context.strip()
            if raw_context.startswith("```"):
                # Extract language hint and inner content
                first_line_end = raw_context.find("\n")
                lang_hint = raw_context[3:first_line_end].strip() if first_line_end != -1 else ""
                inner = raw_context[first_line_end + 1:] if first_line_end != -1 else raw_context[3:]
                if inner.endswith("```"):
                    inner = inner[: inner.rfind("```")]
                raw_context = inner.strip()
            else:
                lang_hint = ""

            # Check if this looks like a diff (has <<<<<< OLD / >>>>>> NEW markers or +/- lines)
            is_diff = (
                "<<<<<< OLD" in raw_context
                or ">>>>>> NEW" in raw_context
                or raw_context.startswith("---")
                or raw_context.startswith("+++")
            )

            if is_diff:
                # Convert internal diff markers to unified diff format for Rich
                diff_lines = []
                in_old = False
                in_new = False
                for line in raw_context.splitlines():
                    if line.strip() == "<<<<<< OLD":
                        in_old = True
                        in_new = False
                        continue
                    elif line.strip() == "======":
                        in_old = False
                        in_new = True
                        continue
                    elif line.strip() == ">>>>>> NEW":
                        in_new = False
                        continue
                    if in_old:
                        diff_lines.append(f"-{line}")
                    elif in_new:
                        diff_lines.append(f"+{line}")
                    else:
                        diff_lines.append(f" {line}")
                content_renderable = Syntax(
                    "\n".join(diff_lines), "diff", theme="monokai", word_wrap=True
                )
            elif lang_hint:
                content_renderable = Syntax(
                    raw_context, lang_hint, theme="monokai", word_wrap=True
                )
            elif "\n" in raw_context or len(raw_context) > 50:
                content_renderable = Markdown(raw_context)
            else:
                content_renderable = Text(f"`{raw_context}`")

            panel_content = Group(content_renderable, Text(""), warning_text)

            panel = Panel(
                panel_content,
                title=f"[bold red]{action_description}[/bold red]",
                border_style="red",
                expand=False,
            )

            console.print(panel)

            # Force blocking input using executor to guarantee wait on Windows/Agent environments
            loop = asyncio.get_running_loop()

            def windows_arrow_menu():
                import msvcrt
                import sys
                import time

                options = [
                    ("Yes", "execute"),
                    ("Yes, and don't ask again for this specific command", "execute_save"),
                    ("Type here to tell the agent what to do differently", "feedback"),
                    ("No, cancel", "cancel"),
                ]
                current_idx = 0

                # ANSI codes
                gray = "\033[90m"
                reset = "\033[0m"
                clear_line = "\033[K"
                up = "\033[F"

                # Clear any potential spinner artifacts from the current line
                sys.stdout.write("\n\n")
                sys.stdout.write("\r" + " " * 120 + "\r")
                sys.stdout.flush()

                print(f" {gray}Do you want to proceed?{reset}")
                print(f" {gray}Esc to cancel{reset}\n")

                # Initial render lines (allocate space)
                for _ in options:
                    print()

                # Move cursor back up to start of options
                for _ in options:
                    sys.stdout.write(up)

                while True:
                    # Redraw options
                    for idx, (label, _) in enumerate(options):
                        prefix = " > " if idx == current_idx else "   "
                        color = "\033[1m" if idx == current_idx else ""  # Bold for selected
                        print(f"{prefix}{color}{idx + 1}. {label}{reset}{clear_line}")

                    # Check for input
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b"\x1b":  # Esc
                            return "cancel"
                        elif key == b"\r":  # Enter
                            _, value = options[current_idx]
                            return value
                        elif key == b"\xe0":  # Special key (arrows)
                            try:
                                key = msvcrt.getch()
                                if key == b"H":  # Up
                                    current_idx = max(0, current_idx - 1)
                                elif key == b"P":  # Down
                                    current_idx = min(len(options) - 1, current_idx + 1)
                            except Exception:
                                pass

                    # Move cursor back up to repaint for next frame
                    for _ in options:
                        sys.stdout.write(up)

                    time.sleep(0.05)

            # Execute the menu in the thread executor
            choice = await loop.run_in_executor(None, windows_arrow_menu)

            if choice == "cancel":
                raise UserCancelledError("User selected 'No, cancel'")

            if choice == "execute_save":
                perm_mgr.save_permission(action_string, "allow")
                console.print(f"[green]Permission saved: {action_string}[/green]")
                console.print("[green]Approved. Executing...[/green]")
                return None

            if choice == "feedback":
                # Use standard input for feedback
                def get_feedback():
                    return input("Enter your feedback for the agent: ")

                loop = asyncio.get_running_loop()
                feedback = await loop.run_in_executor(None, get_feedback)

                return f"User Feedback: {feedback}"

            # If choice is execute
            console.print("[green]Approved. Executing...[/green]")
            return None

        finally:
            # Resume spinner if it was active
            if active_spinner:
                try:
                    VibeSpinner.resume_spinner(active_spinner)
                except Exception:
                    pass

    except ImportError:
        # Fallback
        print(f"\nWARNING: Approval required for: {action_description}")
        print(f"Context: {context}")

        # Run blocking input in executor
        loop = asyncio.get_running_loop()

        def get_input():
            return input("Execute this action? (y/n/feedback): ").lower()

        response = await loop.run_in_executor(None, get_input)

        if response.startswith("n"):
            return "Action cancelled by user."
        if not response.startswith("y"):
            return f"User Feedback: {response}"
        return None
