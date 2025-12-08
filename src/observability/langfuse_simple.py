"""
Simplified Langfuse integration with AutoGen using OpenLit

This is the official and recommended way to integrate Langfuse with AutoGen.
OpenLit automatically captures all AutoGen operations.
"""

import os
from typing import Optional


def init_langfuse_tracing(
        enabled: bool = True,
        debug: bool = False
) -> bool:
    """
    Initialize Langfuse tracing using OpenLit (official method)

    This function automatically configures tracing of all AutoGen operations
    without needing to modify additional code.

    Args:
        enabled: If False, tracing is not initialized
        debug: If True, prints debug information

    Returns:
        True if initialized correctly, False otherwise

    Example:
        >>> from src.observability.langfuse_simple import init_langfuse_tracing
        >>> init_langfuse_tracing()
        True
    """
    if not enabled:
        if debug:
            print("[INFO] Langfuse tracing disabled")
        return False

    try:
        # Check that environment variables are configured
        required_vars = [
            "LANGFUSE_SECRET_KEY",
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_HOST"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            if debug:
                print(f"[WARNING] Missing environment variables: {', '.join(missing_vars)}")
                print("[INFO] Langfuse tracing will not be initialized")
            return False

        # Import Langfuse and OpenLit
        from langfuse import Langfuse
        import openlit

        if debug:
            print("[INFO] Initializing Langfuse client...")

        # Initialize Langfuse client
        langfuse = Langfuse()

        # Check authentication
        if not langfuse.auth_check():
            if debug:
                print("[ERROR] Langfuse authentication failed")
            return False

        if debug:
            print("[OK] Langfuse client authenticated")
            print("[INFO] Initializing OpenLit instrumentation...")

        # Initialize OpenLit with Langfuse tracer
        # OpenLit will automatically capture all AutoGen operations
        # Silence ALL OpenLit and OpenTelemetry logs
        import logging
        import sys

        # Silenciar todos los loggers relacionados con telemetría
        for logger_name in ["openlit", "opentelemetry", "opentelemetry.sdk",
                            "opentelemetry.exporter", "opentelemetry.metrics"]:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            logging.getLogger(logger_name).propagate = False

        # Suppress OpenTelemetry stdout
        import os
        os.environ["OTEL_LOG_LEVEL"] = "CRITICAL"
        os.environ["OTEL_PYTHON_LOG_LEVEL"] = "CRITICAL"

        openlit.init(
            tracer=langfuse._otel_tracer,
            disable_batch=True,  # Process traces immediately
            disable_metrics=True,  # Disable metrics (this should stop JSON output)
        )

        if debug:
            print("[OK] OpenLit instrumentation initialized")
            print("[OK] Langfuse tracing active - all AutoGen operations will be tracked")

        return True

    except ImportError as e:
        if debug:
            print(f"[ERROR] Error importing dependencies: {e}")
            print("[INFO] Install: pip install langfuse openlit")
        return False

    except Exception as e:
        if debug:
            print(f"[ERROR] Error initializing Langfuse: {e}")
        return False


def is_langfuse_enabled() -> bool:
    """
    Check if Langfuse is enabled and configured

    Returns:
        True if environment variables are configured
    """
    required_vars = [
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_HOST"
    ]

    return all(os.getenv(var) for var in required_vars)


# Automatic initialization when importing the module (optional)
# You can comment these lines if you prefer to initialize manually
if __name__ != "__main__":
    # Only initialize if we're not executing this file directly
    pass  # Don't auto-initialize, wait for main.py to do it explicitly
