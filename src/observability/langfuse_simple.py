"""
Simplified Langfuse integration with AutoGen using OpenLit

This is the official and recommended way to integrate Langfuse with AutoGen.
OpenLit automatically captures all AutoGen operations.
"""

import os


def init_langfuse_tracing(enabled: bool = True, debug: bool = False) -> bool:
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

    import os  # Ensure os is available in this scope

    try:
        # Check that environment variables are configured
        required_vars = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_HOST"]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            if debug:
                print(f"[WARNING] Missing environment variables: {', '.join(missing_vars)}")
                print("[INFO] Langfuse tracing will not be initialized")
            return False

        # Import Langfuse and OpenLit
        import openlit
        from langfuse import Langfuse

        if debug:
            print("[INFO] Initializing Langfuse client...")

        # Get user ID for this machine (for separating data from different installations)
        try:
            from src.config.constants import get_machine_name, get_user_id

            user_id = get_user_id()
            machine_name = get_machine_name()
            if debug:
                print(f"[INFO] User ID: {user_id[:8]}... Machine: {machine_name}")
        except Exception:
            user_id = None
            machine_name = "unknown"

        # Initialize Langfuse client with user identification
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
        for logger_name in [
            "openlit",
            "opentelemetry",
            "opentelemetry.sdk",
            "opentelemetry.exporter",
            "opentelemetry.metrics",
        ]:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            logging.getLogger(logger_name).propagate = False

        # Suppress OpenTelemetry stdout
        import os

        os.environ["OTEL_LOG_LEVEL"] = "CRITICAL"
        os.environ["OTEL_PYTHON_LOG_LEVEL"] = "CRITICAL"

        # Initialize OpenLit with user identification metadata
        # Using OTLP direct endpoint for Langfuse v3 compatibility
        lf_host_raw = os.environ.get("LANGFUSE_HOST")
        if lf_host_raw is None:
            if debug:
                print("[ERROR] LANGFUSE_HOST is not set")
            return False
        lf_host = lf_host_raw.rstrip("/")
        lf_pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
        lf_sk = os.environ.get("LANGFUSE_SECRET_KEY")

        import base64

        auth_str = f"{lf_pk}:{lf_sk}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()

        try:
            openlit.init(
                otlp_endpoint=f"{lf_host}/api/public/otel",
                otlp_headers={"Authorization": f"Basic {b64_auth}"},
                disable_batch=True,  # Process traces immediately
                disable_metrics=True,  # Disable metrics (this should stop JSON output)
                environment=f"daveagent-{machine_name}" if machine_name else "daveagent",
                application_name=f"DaveAgent-{user_id[:8]}" if user_id else "DaveAgent",
            )
        except TypeError:
            # Fallback for older OpenLit versions via env vars
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{lf_host}/api/public/otel"
            os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {b64_auth}"
            os.environ["OPENLIT_ENVIRONMENT"] = (
                f"daveagent-{machine_name}" if machine_name else "daveagent"
            )
            os.environ["OPENLIT_APPLICATION_NAME"] = (
                f"DaveAgent-{user_id[:8]}" if user_id else "DaveAgent"
            )
            openlit.init(disable_metrics=True)

        if debug:
            print("[OK] OpenLit instrumentation initialized")
            print("[OK] Langfuse tracing active - all AutoGen operations will be tracked")
            if user_id:
                print(f"[OK] Traces tagged with user: {user_id[:8]}...")

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
    required_vars = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_HOST"]

    return all(os.getenv(var) for var in required_vars)


# Automatic initialization when importing the module (optional)
# You can comment these lines if you prefer to initialize manually
if __name__ != "__main__":
    # Only initialize if we're not executing this file directly
    pass  # Don't auto-initialize, wait for main.py to do it explicitly
