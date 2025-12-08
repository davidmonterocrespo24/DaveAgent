"""
Specialized memory types for different use cases
"""

from autogen_core.memory import Memory, MemoryContent
from typing import List, Optional, Dict, Any


class ConversationMemory:
    """
    Wrapper for conversation-specific memory operations
    """

    def __init__(self, memory: Memory):
        self.memory = memory

    async def add_exchange(
        self,
        user_input: str,
        agent_response: str,
        agents_used: Optional[List[str]] = None,
        tools_called: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """
        Add a conversation exchange with rich metadata

        Args:
            user_input: User's request
            agent_response: Agent's response
            agents_used: List of agents that participated
            tools_called: List of tools that were called
            **kwargs: Additional metadata
        """
        # Memory is added via MemoryManager, this is a helper wrapper
        pass

    async def query(self, query: str) -> List[MemoryContent]:
        """Query conversation memory"""
        return await self.memory.query(query)


class CodebaseMemory:
    """
    Wrapper for codebase-specific memory operations
    """

    def __init__(self, memory: Memory):
        self.memory = memory

    async def add_file(
        self,
        file_path: str,
        content: str,
        language: str,
        functions: Optional[List[str]] = None,
        classes: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """
        Add a code file with extracted metadata

        Args:
            file_path: Path to the source file
            content: File content
            language: Programming language
            functions: List of function names in the file
            classes: List of class names in the file
            **kwargs: Additional metadata
        """
        pass

    async def query(self, query: str) -> List[MemoryContent]:
        """Query codebase memory"""
        return await self.memory.query(query)


class DecisionMemory:
    """
    Wrapper for decision-specific memory operations
    """

    def __init__(self, memory: Memory):
        self.memory = memory

    async def add_decision(
        self,
        decision: str,
        context: str,
        category: str = "architecture",
        impact: str = "medium",
        **kwargs,
    ) -> None:
        """
        Add an architectural or technical decision

        Args:
            decision: The decision made
            context: Context and reasoning
            category: Decision category (architecture, design, implementation, etc.)
            impact: Impact level (low, medium, high)
            **kwargs: Additional metadata
        """
        pass

    async def query(self, query: str) -> List[MemoryContent]:
        """Query decision memory"""
        return await self.memory.query(query)


class UserPreferencesMemory:
    """
    Wrapper for user preferences memory operations
    """

    def __init__(self, memory: Memory):
        self.memory = memory

    async def add_preference(
        self, preference: str, category: str = "general", priority: str = "normal", **kwargs
    ) -> None:
        """
        Add a user preference

        Args:
            preference: The preference statement
            category: Preference category (code_style, framework, tool, workflow, etc.)
            priority: Priority level (low, normal, high)
            **kwargs: Additional metadata
        """
        pass

    async def query(self, query: str) -> List[MemoryContent]:
        """Query preferences memory"""
        return await self.memory.query(query)

    async def get_all_preferences(self) -> List[MemoryContent]:
        """Get all stored preferences"""
        # Query with a broad term to get all preferences
        return await self.query("preference")
