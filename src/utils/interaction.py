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
        active_spinner = VibeSpinner.pause_active_spinner()
        
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
            
            # Use InquirerPy for arrow key navigation
            options = [
                Choice("execute", "Yes, execute now"),
                Choice("cancel", "No, cancel"),
                Choice("feedback", "Type feedback")
            ]
            
            # Use execute_async to run in the existing event loop
            try:
                choice = await inquirer.select(
                    message="Select an option:",
                    choices=options,
                    default="execute",
                    pointer=">",
                ).execute_async()
            except AttributeError:
                # Fallback if execute_async is not available (older versions)
                # Run sync execute() in a thread to avoid blocking the loop
                loop = asyncio.get_running_loop()
                prompt = inquirer.select(
                    message="Select an option:",
                    choices=options,
                    default="execute",
                    pointer=">",
                )
                choice = await loop.run_in_executor(None, prompt.execute)
            
            if choice == "cancel":
                return "Action cancelled by user."
            
            if choice == "feedback":
                # Use standard input or prompt for feedback
                try:
                    feedback = await inquirer.text(message="Enter your feedback for the agent:").execute_async()
                except AttributeError:
                    loop = asyncio.get_running_loop()
                    prompt = inquirer.text(message="Enter your feedback for the agent:")
                    feedback = await loop.run_in_executor(None, prompt.execute)

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
