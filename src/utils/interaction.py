"""
Interaction utilities for Human-in-the-Loop approval.
"""

import sys

from src.utils.errors import UserCancelledError


async def ask_for_approval(action_description: str, context: str = ""):
    """
    Interactively asks the user for approval to execute an action.

    Args:
        action_description: A short summary of the action (e.g., "Execute command...").
        context: Detailed context or code block to display (e.g., the command itself).

    Returns:
        None if approved.
        A string message if cancelled or if feedback is provided.
    """
    import sys
    import time
    import asyncio

    # Check if running in headless mode (subagents/background tasks)
    from src.utils.headless_context import is_headless
    if is_headless():
        # Auto-approve in headless mode (no user interaction)
        return None

    try:
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.text import Text

        from src.utils.permissions import get_permission_manager

        # Import VibeSpinner and WindowsSafeConsole
        from src.utils.vibe_spinner import VibeSpinner, WindowsSafeConsole

        # Use WindowsSafeConsole to ensure VT processing is enabled before each print
        console = WindowsSafeConsole()
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
        # Pause active spinner during user interaction and prevent new ones from starting
        active_spinner = VibeSpinner.suspend_for_interaction()

        # CRITICAL: Clear spinner artifacts and move to new line
        # This prevents spinner from overlapping with approval dialog
        import time
        time.sleep(0.05)  # Give spinner time to stop
        sys.stdout.write("\r" + " " * 150 + "\r")  # Clear current line
        sys.stdout.write("\n")  # Move to new line to ensure clean slate
        sys.stdout.flush()

        try:
            from rich.syntax import Syntax

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

            # Limit content height to prevent panel from being too large
            # This ensures options stay visible without scrolling
            max_content_lines = 15
            content_lines = raw_context.splitlines()

            if len(content_lines) > max_content_lines:
                # Truncate and add indicator
                truncated_context = "\n".join(content_lines[:max_content_lines])
                truncated_context += f"\n... ({len(content_lines) - max_content_lines} more lines)"
                raw_context = truncated_context

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

            # Remove warning text from panel to make it more compact
            panel_content = content_renderable

            panel = Panel(
                panel_content,
                title=f"[bold red]{action_description}[/bold red]",
                border_style="red",
                expand=False,
            )

            console.print(panel)

            # Ensure clean separation before menu
            import sys
            import time

            # Force all pending output to flush
            sys.stdout.flush()
            sys.stderr.flush()

            # Wait for any pending output to complete
            time.sleep(0.1)

            # CRITICAL FIX: Ensure Windows VT processing is enabled BEFORE questionary
            # questionary uses prompt_toolkit which requires ANSI escape sequences
            # Without this, options will be invisible on Windows
            from src.utils.vibe_spinner import _ensure_windows_vt_processing
            _ensure_windows_vt_processing()

            # Use questionary instead of pick - much better scroll behavior
            # questionary doesn't hijack the screen like curses-based pick
            import questionary
            from questionary import Style

            # Custom style to ensure visibility on Windows
            custom_style = Style([
                ('qmark', 'fg:#673ab7 bold'),       # Question mark
                ('question', 'bold'),                # Question text
                ('answer', 'fg:#f44336 bold'),       # Selected answer
                ('pointer', 'fg:#673ab7 bold'),      # Pointer (>)
                ('highlighted', 'fg:#673ab7 bold'),  # Highlighted option
                ('selected', 'fg:#cc5454'),          # Selected checkbox
                ('separator', 'fg:#cc5454'),         # Separator
                ('instruction', ''),                 # Instruction text
                ('text', ''),                        # Plain text
                ('disabled', 'fg:#858585 italic')    # Disabled options
            ])

            # Define choices for questionary
            choices = [
                questionary.Choice("Yes", value="execute"),
                questionary.Choice("Yes, and don't ask again for this specific command", value="execute_save"),
                questionary.Choice("Type feedback to tell the agent what to do differently", value="feedback"),
                questionary.Choice("No, cancel", value="cancel"),
            ]

            # Run questionary in executor to avoid blocking async loop
            def run_questionary():
                # Ensure VT processing one more time right before questionary runs
                _ensure_windows_vt_processing()

                return questionary.select(
                    "Do you want to proceed?",
                    choices=choices,
                    style=custom_style,
                    use_arrow_keys=True,
                    use_shortcuts=False,
                    use_indicator=True,
                ).ask()

            loop = asyncio.get_running_loop()
            choice = await loop.run_in_executor(None, run_questionary)

            # Re-enable VT processing after questionary (in case it got disabled)
            _ensure_windows_vt_processing()

            # Questionary doesn't leave artifacts, but ensure clean output
            sys.stdout.flush()

            if choice == "cancel":
                raise UserCancelledError("User selected 'No, cancel'")

            if choice == "execute_save":
                perm_mgr.save_permission(action_string, "allow")
                console.print(f"[green]Permission saved: {action_string}[/green]")
                console.print("[green]Approved. Executing...[/green]")
                return None

            if choice == "feedback":
                # Clear the line and ask for feedback with standard input
                console.print("\n[cyan]Enter your feedback for the agent:[/cyan]")

                def get_feedback():
                    return input("> ")

                loop = asyncio.get_running_loop()
                feedback = await loop.run_in_executor(None, get_feedback)

                return f"User Feedback: {feedback}"

            # If choice is execute
            console.print("[green]Approved. Executing...[/green]")
            return None

        finally:
            # Resume spinner if it was active
            try:
                VibeSpinner.resume_from_interaction(active_spinner)
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
