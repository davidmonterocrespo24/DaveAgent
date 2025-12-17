"""
Interaction utilities for Human-in-the-Loop approval.
"""
from typing import Optional, Tuple



async def ask_for_approval(action_description: str, context: str = "") -> Optional[str]:
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
    try:
        from rich.console import Console, Group
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich.text import Text
        # Import InquirerPy for arrow key support
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice
        
        # Import VibeSpinner to pause animation
        from src.utils.vibe_spinner import VibeSpinner
        
        console = Console()
        
        # Pause any active spinner to prevent interference
        # Robustly search for any VibeSpinner class in sys.modules to handle import mismatches
        import sys
        active_spinner = None
        
        # 1. Try standard import pause
        active_spinner = VibeSpinner.pause_active_spinner()
        
        # 2. If not found, try searching sys.modules for other instances
        if not active_spinner:
            for module_name, module in list(sys.modules.items()):
                if 'vibe_spinner' in module_name and hasattr(module, 'VibeSpinner'):
                    try:
                        possible_cls = getattr(module, 'VibeSpinner')
                        if possible_cls is not VibeSpinner: # Only if it's a different class object
                            found = possible_cls.pause_active_spinner()
                            if found:
                                active_spinner = found
                                break
                    except: pass
        
        try:
            # Format the context
            if "\n" in context or len(context) > 50:
                 context_display = context 
            else:
                 context_display = f"`{context}`"

            warning_text = Text(
                "WARNING: This action requires approval.", style="bold yellow"
            )

            # Use Group to correctly render Markdown + Text inside Panel
            panel_content = Group(
                Markdown(context_display),
                Text("\n"),
                warning_text
            )

            panel = Panel(
                panel_content,
                title=f"[bold red]{action_description}[/bold red]",
                border_style="red",
                expand=False
            )
            
            console.print(panel)
            
            # Force blocking input using executor to guarantee wait on Windows/Agent environments
            loop = asyncio.get_running_loop()
            
            # Force blocking input using executor to guarantee wait on Windows/Agent environments
            # Custom Arrow Key Menu for Windows (Mimicking Claude CLI)
            loop = asyncio.get_running_loop()
            
            def windows_arrow_menu():
                import msvcrt
                import sys
                import time

                options = [
                    ("Yes", "execute"),
                    ("Yes, allow all edits during this session (not implemented)", "execute_all"),
                    ("Type here to tell the agent what to do differently", "feedback"),
                    ("No, cancel", "cancel")
                ]
                current_idx = 0
                
                # ANSI codes
                gray = "\033[90m"
                reset = "\033[0m"
                clear_line = "\033[K"
                up = "\033[F"
                
                # Clear any potential spinner artifacts from the current line
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
                        color = "\033[1m" if idx == current_idx else "" # Bold for selected
                        print(f"{prefix}{color}{idx + 1}. {label}{reset}{clear_line}")
                    
                    # Check for input
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'\x1b': # Esc
                            return 'cancel'
                        elif key == b'\r': # Enter
                            _, value = options[current_idx]
                            return value
                        elif key == b'\xe0': # Special key (arrows)
                            try:
                                key = msvcrt.getch()
                                if key == b'H': # Up
                                    current_idx = max(0, current_idx - 1)
                                elif key == b'P': # Down
                                    current_idx = min(len(options) - 1, current_idx + 1)
                            except: pass
                    
                    # Move cursor back up to repaint for next frame
                    for _ in options:
                        sys.stdout.write(up)
                    
                    time.sleep(0.05)
            
            # Execute the menu in the thread executor
            choice = await loop.run_in_executor(None, windows_arrow_menu)
            
            if choice == "cancel":
                return "Action cancelled by user."
            
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
            # Resume spinner if it was running
            VibeSpinner.resume_spinner(active_spinner)

    except ImportError:
        # Fallback
        print(f"\nWARNING: Approval required for: {action_description}")
        print(f"Context: {context}")
        
        # Run blocking input in executor
        loop = asyncio.get_running_loop()
        def get_input():
            return input("Execute this action? (y/n/feedback): ").lower()
            
        response = await loop.run_in_executor(None, get_input)
        
        if response.startswith('n'):
            return "Action cancelled by user."
        if not response.startswith('y'):
            return f"User Feedback: {response}"
        return None
