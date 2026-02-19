"""
Headless Context Manager

Manages global headless state for disabling user prompts in background/subagent execution.
Uses contextvars for async-safe context management.
"""

import contextvars

# Context variable for headless mode (async-safe)
_headless_mode = contextvars.ContextVar('headless_mode', default=False)


def set_headless(enabled: bool) -> None:
    """Set headless mode for current context.

    Args:
        enabled: True to enable headless (no user prompts), False for interactive
    """
    _headless_mode.set(enabled)


def is_headless() -> bool:
    """Check if currently running in headless mode.

    Returns:
        True if headless mode is enabled, False otherwise
    """
    return _headless_mode.get()
