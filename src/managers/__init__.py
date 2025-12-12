"""
System managers - State, Context, and RAG
"""

from src.managers.state_manager import StateManager
from src.managers.context_manager import ContextManager

# Avoid importing RAGManager here to prevent heavy dependencies (chromadb, sentence-transformers)
# from loading when only StateManager or ContextManager are needed.
# RAGManager should be imported directly from src.managers.rag_manager when needed.
try:
    __all__ = ["StateManager", "ContextManager"]
except ImportError:
    __all__ = ["StateManager", "ContextManager"]

from src.managers.issue_reporter import IssueReporter
__all__.append("IssueReporter")
