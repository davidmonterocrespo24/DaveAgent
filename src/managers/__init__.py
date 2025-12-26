"""
System managers - State, Context, RAG, and Error Reporting
"""

from src.managers.context_manager import ContextManager
from src.managers.error_reporter import ErrorReporter
from src.managers.state_manager import StateManager

# Avoid importing RAGManager here to prevent heavy dependencies (chromadb, sentence-transformers)
# from loading when only StateManager or ContextManager are needed.
# RAGManager should be imported directly from src.managers.rag_manager when needed.

__all__ = ["StateManager", "ContextManager", "ErrorReporter"]
