"""
Observability module with Langfuse

This module provides integration with Langfuse for traceability
and monitoring of AutoGen agents.

There are two ways to use Langfuse:

1. **Simple (Recommended)**: Using OpenLit - automatic tracking
   from src.observability import init_langfuse_tracing
   init_langfuse_tracing()

2. **Advanced**: Using LangfuseTracker - manual control
   from src.observability import LangfuseTracker
   tracker = LangfuseTracker()
"""

from .langfuse_simple import init_langfuse_tracing, is_langfuse_enabled

# Only export the simple method with OpenLit (recommended)
__all__ = [
    "init_langfuse_tracing",      # Simple method with OpenLit (recommended)
    "is_langfuse_enabled",         # Verify configuration
]
