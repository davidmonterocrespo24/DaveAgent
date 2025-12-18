"""
Vibe Spinner - Animated spinner with rotating vibe messages
Shows creative messages while the agent is thinking/working
"""

import random
import sys
import threading
import time

# Global registry for active spinner (module level for safety across imports)
_GLOBAL_ACTIVE_SPINNER = None
_ALL_SPINNERS = set()


class VibeSpinner:
    """Animated spinner with rotating creative messages"""

    # Vibe messages in English and Spanish
    VIBE_MESSAGES_EN = [
        "vibing",
        "creating",
        "imagining",
        "coding",
        "designing",
        "building",
        "innovating",
        "exploring",
        "dreaming",
        "inspiring",
        "connecting",
        "flowing",
        "discovering",
        "transforming",
        "learning",
        "sharing",
        "thinking",
        "analyzing",
        "visualizing",
        "reinventing",
        "experimenting",
        "developing",
        "growing",
        "evolving",
        "expressing",
        "composing",
        "observing",
        "creating together",
        "making magic",
        "shaping ideas",
        "building dreams",
        "crafting code",
        "pushing limits",
        "feeling the flow",
        "embracing change",
    ]

    VIBE_MESSAGES_ES = [
        "vibing",
        "creating",
        "imagining",
        "coding",
        "designing",
        "building",
        "innovating",
        "exploring",
        "dreaming",
        "inspiring",
        "connecting",
        "flowing",
        "discovering",
        "transforming",
        "learning",
        "sharing",
        "thinking",
        "analyzing",
        "visualizing",
        "reinventing",
        "experimenting",
        "developing",
        "growing",
        "evolving",
        "expressing",
        "composing",
        "observing",
        "creating together",
        "making magic",
        "shaping ideas",
        "building dreams",
        "crafting code",
        "pushing limits",
        "feeling the flow",
        "embracing change",
    ]

    # Spinner characters (different styles)
    SPINNERS = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["-", "\\", "|", "/"],
        "circle": ["◐", "◓", "◑", "◒"],
        "arrow": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        "dots2": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
        "box": ["◰", "◳", "◲", "◱"],
        "bounce": ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"],
    }

    COLORS = {
        "cyan": "\033[96m",
        "blue": "\033[94m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "magenta": "\033[95m",
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    }

    @classmethod
    def set_active_spinner(cls, spinner):
        global _GLOBAL_ACTIVE_SPINNER
        _GLOBAL_ACTIVE_SPINNER = spinner

    @classmethod
    def clear_active_spinner(cls):
        global _GLOBAL_ACTIVE_SPINNER
        _GLOBAL_ACTIVE_SPINNER = None

    @classmethod
    def pause_active_spinner(cls):
        """Pauses ANY active spinner instance"""
        global _GLOBAL_ACTIVE_SPINNER, _ALL_SPINNERS

        paused_spinner = None

        # 1. Check primary global
        if _GLOBAL_ACTIVE_SPINNER and _GLOBAL_ACTIVE_SPINNER.is_running():
            _GLOBAL_ACTIVE_SPINNER.stop(clear_line=True)
            paused_spinner = _GLOBAL_ACTIVE_SPINNER

        # 2. Check ALL known instances (Nuclear Option for ghosts)
        # Use list copy to avoid modification during iteration if needed
        for spinner in list(_ALL_SPINNERS):
            if spinner.is_running():
                spinner.stop(clear_line=True)
                if not paused_spinner:
                    paused_spinner = spinner

        return paused_spinner

    @classmethod
    def resume_spinner(cls, spinner):
        """Resumes a paused spinner"""
        if spinner:
            spinner.start()

    def __init__(
        self,
        messages: list[str] | None = None,
        *,
        spinner_style: str = "dots",
        color: str = "cyan",
        language: str = "es",
        update_interval: float = 0.1,
        message_interval: float = 2.0,
    ):
        """
        Initialize the vibe spinner

        Args:
            messages: Custom list of messages (uses default if None)
            spinner_style: Style of spinner animation
            color: Color of the spinner
            language: Language for default messages ("en" or "es")
            update_interval: How fast the spinner rotates (seconds)
            message_interval: How often to change the message (seconds)
        """
        # Choose messages
        if messages:
            self.messages = messages
        else:
            self.messages = self.VIBE_MESSAGES_ES if language == "es" else self.VIBE_MESSAGES_EN

        self.spinner_chars = self.SPINNERS.get(spinner_style, self.SPINNERS["dots"])
        self.color = self.COLORS.get(color, self.COLORS["cyan"])
        self.update_interval = update_interval
        self.message_interval = message_interval

        # Register in global list
        global _ALL_SPINNERS
        _ALL_SPINNERS.add(self)

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_message_index = 0
        self._spinner_index = 0
        self._last_message_change = time.time()

    def _animate(self):
        """Animation loop that runs in a separate thread"""
        while not self._stop_event.is_set():
            # Get current message
            message = self.messages[self._current_message_index]

            # Get current spinner character
            spinner_char = self.spinner_chars[self._spinner_index]

            # Build the output line
            output = (
                f"\r{self.color}{self.COLORS['bold']}"
                f"{spinner_char} {message}...{self.COLORS['reset']}"
                f"  {self.COLORS['dim']}(thinking){self.COLORS['reset']}"
            )

            # Write to stdout
            sys.stdout.write(output)
            sys.stdout.flush()

            # Update spinner character
            self._spinner_index = (self._spinner_index + 1) % len(self.spinner_chars)

            # Check if it's time to change the message
            current_time = time.time()
            if current_time - self._last_message_change >= self.message_interval:
                self._current_message_index = (self._current_message_index + 1) % len(self.messages)
                self._last_message_change = current_time

            # Sleep
            time.sleep(self.update_interval)

    def start(self):
        """Start the spinner animation"""
        if self._thread is not None and self._thread.is_alive():
            return  # Already running

        # REGISTER AS ACTIVE SPINNER
        VibeSpinner.set_active_spinner(self)

        # Randomize starting message for variety
        self._current_message_index = random.randint(0, len(self.messages) - 1)
        self._spinner_index = 0
        self._last_message_change = time.time()
        self._stop_event.clear()

        # Start animation thread
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self, clear_line: bool = True):
        """
        Stop the spinner animation

        Args:
            clear_line: Whether to clear the spinner line
        """
        # CLEAR ACTIVE SPINNER
        VibeSpinner.clear_active_spinner()

        if self._thread is None or not self._thread.is_alive():
            return  # Not running

        # Signal thread to stop
        self._stop_event.set()

        # Wait for thread to finish
        self._thread.join(timeout=1.0)

        if clear_line:
            # Clear the line (use more spaces to ensure full cleanup)
            sys.stdout.write("\r" + " " * 120 + "\r")
            sys.stdout.flush()

    def update_message(self, message: str):
        """
        Manually update the current message

        Args:
            message: New message to display
        """
        if message not in self.messages:
            self.messages.append(message)
        self._current_message_index = self.messages.index(message)
        self._last_message_change = time.time()

    def is_running(self) -> bool:
        """Check if spinner is currently running"""
        return self._thread is not None and self._thread.is_alive()

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False


# Convenience function
def show_vibe_spinner(
    message: str | None = None, style: str = "dots", color: str = "cyan", language: str = "es"
) -> VibeSpinner:
    """
    Create and start a vibe spinner

    Args:
        message: Custom single message (uses rotating messages if None)
        style: Spinner style
        color: Spinner color
        language: Language for messages

    Returns:
        Running VibeSpinner instance
    """
    messages = [message] if message else None
    spinner = VibeSpinner(messages=messages, spinner_style=style, color=color, language=language)
    spinner.start()
    return spinner
