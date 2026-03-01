"""
Vibe Spinner - Animated spinner with rotating vibe messages
Shows creative messages while the agent is thinking/working
"""

import random
import sys
import threading
import time

# Global registry for active spinner (module level for safety across imports)
_GLOBAL_ACTIVE_SPINNER: "VibeSpinner | None" = None
_ALL_SPINNERS: set["VibeSpinner"] = set()


def _ensure_windows_vt_processing():
    """
    Ensure Windows Virtual Terminal Processing is enabled.

    Rich's Status.stop() and prompt_toolkit's patch_stdout() both reset the
    Windows console mode, which strips ENABLE_VIRTUAL_TERMINAL_PROCESSING.
    Without this flag, all ANSI escape codes (colors, box-drawing) are
    displayed as raw text like ?[36m instead of being interpreted.

    This function performs a lazy check - only sets the mode if not already enabled.
    Safe to call on non-Windows platforms (no-op).
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32

        # Process both STDOUT and STDERR
        for std_handle in [-11, -12]:  # STD_OUTPUT_HANDLE, STD_ERROR_HANDLE
            handle = kernel32.GetStdHandle(std_handle)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))

            # VT processing flags
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            DISABLE_NEWLINE_AUTO_RETURN = 0x0008

            # ALWAYS set the mode (not lazy) to ensure it's enabled
            # The lazy check wasn't working reliably after patch_stdout()
            new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING | DISABLE_NEWLINE_AUTO_RETURN
            result = kernel32.SetConsoleMode(handle, new_mode)

            # Verify it was set correctly
            if result == 0:
                # SetConsoleMode failed, try to get error
                error_code = kernel32.GetLastError()
                # Silently continue - don't crash on error
    except Exception:
        pass


class WindowsSafeConsole:
    """
    Console wrapper that ensures VT mode is enabled before printing.

    This is a lightweight wrapper around rich.console.Console that checks
    and enables Windows VT processing before each print operation.
    Fully supports context manager protocol and all Console methods.
    """

    def __init__(self, *args, **kwargs):
        from rich.console import Console

        self._console = Console(*args, **kwargs)

    def print(self, *args, **kwargs):
        """Override print to ensure VT processing before output"""
        _ensure_windows_vt_processing()  # Ensure VT mode is enabled
        result = self._console.print(*args, **kwargs)
        # Force flush after every print to ensure visibility
        import sys

        sys.stdout.flush()
        return result

    def log(self, *args, **kwargs):
        """Override log to ensure VT processing before output"""
        _ensure_windows_vt_processing()
        return self._console.log(*args, **kwargs)

    def out(self, *args, **kwargs):
        """Override out to ensure VT processing before output"""
        _ensure_windows_vt_processing()
        return self._console.out(*args, **kwargs)

    def __enter__(self):
        """Support context manager protocol"""
        _ensure_windows_vt_processing()
        return self._console.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support context manager protocol"""
        result = self._console.__exit__(exc_type, exc_val, exc_tb)
        _ensure_windows_vt_processing()  # Re-enable after context exit
        return result

    def __getattr__(self, name):
        """Delegate all other attributes to the underlying Console"""
        return getattr(self._console, name)


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
        # Note: No 'global' needed as we only read these variables, not reassign them
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

    # --- Interaction Locks ---
    _interaction_suspended = False
    _pending_spinner = None

    @classmethod
    def suspend_for_interaction(cls):
        """Globally suspends spinners from starting and pauses any active ones"""
        cls._interaction_suspended = True
        return cls.pause_active_spinner()

    @classmethod
    def resume_from_interaction(cls, spinner_to_resume=None):
        """Allows spinners to start again, resuming the provided one or pending ones"""
        cls._interaction_suspended = False
        if cls._pending_spinner:
            cls._pending_spinner.start()
            cls._pending_spinner = None
        elif spinner_to_resume:
            cls.resume_spinner(spinner_to_resume)

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
        Initialize the vibe spinner using Rich Status

        Args:
            messages: Custom list of messages (uses default if None)
            spinner_style: Style of spinner animation
            color: Color of the spinner
            language: Language for default messages ("en" or "es")
            update_interval: How fast the spinner rotates (seconds) (Ignored by Rich)
            message_interval: How often to change the message (seconds)
        """
        # Choose messages
        if messages:
            self.messages = messages
        else:
            self.messages = self.VIBE_MESSAGES_ES if language == "es" else self.VIBE_MESSAGES_EN

        self.message_interval = message_interval

        # Register in global list
        _ALL_SPINNERS.add(self)

        from rich.status import Status

        # Use WindowsSafeConsole to ensure VT processing is maintained
        self.console = WindowsSafeConsole(stderr=True)
        self.status = Status(
            self.messages[0], console=self.console, spinner=spinner_style, spinner_style=color
        )

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_message_index = 0
        self._is_running = False

    def _update_message_loop(self):
        """Loop that updates the Rich Status message periodically"""
        last_change = time.time()
        try:
            while not self._stop_event.is_set():
                current_time = time.time()
                if current_time - last_change >= self.message_interval:
                    self._current_message_index = (self._current_message_index + 1) % len(
                        self.messages
                    )
                    message = self.messages[self._current_message_index]
                    # Update the rich status text safely
                    self.status.update(f"{message}...  [dim](thinking)[/dim]")
                    last_change = current_time
                time.sleep(0.1)
        except Exception:
            pass

    def start(self):
        """Start the spinner animation"""
        if self._is_running:
            return

        if VibeSpinner._interaction_suspended:
            VibeSpinner._pending_spinner = self
            return

        self._is_running = True
        self._stop_event.clear()

        # REGISTER AS ACTIVE SPINNER
        VibeSpinner.set_active_spinner(self)

        # Randomize starting message for variety
        self._current_message_index = random.randint(0, len(self.messages) - 1)

        # Start the underlying Rich Status context manager manually
        initial_msg = f"{self.messages[self._current_message_index]}...  [dim](thinking)[/dim]"
        self.status.update(initial_msg)
        self.status.start()

        # Start our lightweight message rotation thread (only if multiple messages)
        if len(self.messages) > 1:
            self._thread = threading.Thread(target=self._update_message_loop, daemon=True)
            self._thread.start()

    def stop(self, clear_line: bool = True):
        """Stop the spinner animation"""
        # CLEAR ACTIVE SPINNER
        VibeSpinner.clear_active_spinner()

        if not self._is_running:
            return

        self._is_running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)

        # Stop the Rich Status
        self.status.stop()

        # CRITICAL: Rich Status.stop() resets Windows console mode, disabling
        # VT processing. Re-enable it so subsequent Rich output renders colors.
        _ensure_windows_vt_processing()

    def update_message(self, message: str):
        """
        Manually update the current message

        Args:
            message: New message to display
        """
        if message not in self.messages:
            self.messages.append(message)
        self._current_message_index = self.messages.index(message)
        self.status.update(f"{message}...  [dim](thinking)[/dim]")

    def is_running(self) -> bool:
        """Check if spinner is currently running"""
        return self._is_running

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
