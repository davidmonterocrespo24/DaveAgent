"""
Base Memory Manager - Central memory system using ChromaDB
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.memory.chromadb import (
    ChromaDBVectorMemory,
    PersistentChromaDBVectorMemoryConfig,
    SentenceTransformerEmbeddingFunctionConfig,
)


class MemoryManager:
    """
    Central memory manager for DaveAgent

    Manages multiple ChromaDB collections for different types of memory:
    - Conversations: Historical conversations and context
    - Codebase: Indexed code files and functions
    - Decisions: Architectural decisions and patterns
    - Preferences: User preferences and coding styles
    """

    def __init__(
            self,
            persistence_path: Optional[str] = None,
            embedding_model: str = "all-MiniLM-L6-v2",
            k: int = 5,
            score_threshold: float = 0.3,
    ):
        """
        Initialize the memory manager

        Args:
            persistence_path: Path to store ChromaDB data (defaults to .daveagent/memory in workspace)
            embedding_model: Sentence transformer model for embeddings
            k: Number of results to retrieve per query
            score_threshold: Minimum similarity score for retrieval
        """
        self.logger = logging.getLogger(__name__)

        # Set up persistence path (workspace-relative, like logs and state)
        if persistence_path is None:
            persistence_path = str(Path(".daveagent") / "memory")

        self.persistence_path = Path(persistence_path)
        self.persistence_path.mkdir(parents=True, exist_ok=True)

        self.embedding_model = embedding_model
        self.k = k
        self.score_threshold = score_threshold

        # Initialize memory stores (lazy loading)
        self._conversation_memory: Optional[ChromaDBVectorMemory] = None
        self._codebase_memory: Optional[ChromaDBVectorMemory] = None
        self._decision_memory: Optional[ChromaDBVectorMemory] = None
        self._preferences_memory: Optional[ChromaDBVectorMemory] = None
        self._user_memory: Optional[ChromaDBVectorMemory] = None

        self.logger.info(f"📚 MemoryManager initialized with persistence path: {self.persistence_path}")

    def _create_memory_store(self, collection_name: str) -> ChromaDBVectorMemory:
        """Create a ChromaDB memory store with the given collection name"""
        try:
            config = PersistentChromaDBVectorMemoryConfig(
                collection_name=collection_name,
                persistence_path=str(self.persistence_path),
                k=self.k,
                score_threshold=self.score_threshold,
                embedding_function_config=SentenceTransformerEmbeddingFunctionConfig(
                    model_name=self.embedding_model
                ),
            )

            memory = ChromaDBVectorMemory(config=config)
            self.logger.debug(f"✓ Created memory store: {collection_name}")
            return memory

        except Exception as e:
            self.logger.error(f"Failed to create memory store {collection_name}: {e}")
            raise

    # =========================================================================
    # Conversation Memory - Historical conversations
    # =========================================================================

    @property
    def conversation_memory(self) -> ChromaDBVectorMemory:
        """Get or create conversation memory store"""
        if self._conversation_memory is None:
            self._conversation_memory = self._create_memory_store("conversations")
        return self._conversation_memory

    async def add_conversation(
            self,
            user_input: str,
            agent_response: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation exchange to memory

        Args:
            user_input: The user's request
            agent_response: The agent's response
            metadata: Additional metadata (agent name, tools used, etc.)
        """
        try:
            # Combine user input and response for better context
            conversation_text = f"USER: {user_input}\n\nAGENT: {agent_response}"

            mem_metadata = metadata or {}
            mem_metadata.update({
                "type": "conversation",
                "user_input": user_input[:200],  # Store preview
                "response_preview": agent_response[:200]
            })

            await self.conversation_memory.add(
                MemoryContent(
                    content=conversation_text,
                    mime_type=MemoryMimeType.TEXT,
                    metadata=mem_metadata
                )
            )

            self.logger.debug(f"💬 Conversation added to memory")

        except Exception as e:
            self.logger.error(f"Failed to add conversation to memory: {e}")

    async def query_conversations(self, query: str) -> List[MemoryContent]:
        """Query conversation memory for relevant past conversations"""
        try:
            results = await self.conversation_memory.query(query)
            count = len(results.results) if hasattr(results, 'results') else len(results)
            self.logger.debug(f"🔍 Found {count} relevant conversations")
            return results
        except Exception as e:
            self.logger.error(f"Failed to query conversations: {e}")
            return []

    # =========================================================================
    # Codebase Memory - Indexed code knowledge
    # =========================================================================

    @property
    def codebase_memory(self) -> ChromaDBVectorMemory:
        """Get or create codebase memory store"""
        if self._codebase_memory is None:
            self._codebase_memory = self._create_memory_store("codebase")
        return self._codebase_memory

    async def add_code_chunk(
            self,
            code: str,
            file_path: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a code chunk to memory

        Args:
            code: The code content
            file_path: Path to the source file
            metadata: Additional metadata (functions, classes, etc.)
        """
        try:
            mem_metadata = metadata or {}
            mem_metadata.update({
                "type": "code",
                "file_path": file_path,
                "language": self._detect_language(file_path)
            })

            await self.codebase_memory.add(
                MemoryContent(
                    content=code,
                    mime_type=MemoryMimeType.TEXT,
                    metadata=mem_metadata
                )
            )

            self.logger.debug(f"📝 Code chunk added: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to add code chunk: {e}")

    async def query_codebase(self, query: str) -> List[MemoryContent]:
        """Query codebase memory for relevant code"""
        try:
            results = await self.codebase_memory.query(query)
            count = len(results.results) if hasattr(results, 'results') else len(results)
            self.logger.debug(f"🔍 Found {count} relevant code chunks")
            return results
        except Exception as e:
            self.logger.error(f"Failed to query codebase: {e}")
            return []

    # =========================================================================
    # Decision Memory - Architectural decisions and patterns
    # =========================================================================

    @property
    def decision_memory(self) -> ChromaDBVectorMemory:
        """Get or create decision memory store"""
        if self._decision_memory is None:
            self._decision_memory = self._create_memory_store("decisions")
        return self._decision_memory

    async def add_decision(
            self,
            decision: str,
            context: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an architectural decision to memory

        Args:
            decision: The decision made
            context: Context and reasoning for the decision
            metadata: Additional metadata
        """
        try:
            decision_text = f"DECISION: {decision}\n\nCONTEXT: {context}"

            mem_metadata = metadata or {}
            mem_metadata.update({
                "type": "decision",
                "decision_summary": decision[:200]
            })

            await self.decision_memory.add(
                MemoryContent(
                    content=decision_text,
                    mime_type=MemoryMimeType.TEXT,
                    metadata=mem_metadata
                )
            )

            self.logger.debug(f"🎯 Decision added to memory")

        except Exception as e:
            self.logger.error(f"Failed to add decision: {e}")

    async def query_decisions(self, query: str) -> List[MemoryContent]:
        """Query decision memory for relevant past decisions"""
        try:
            results = await self.decision_memory.query(query)
            count = len(results.results) if hasattr(results, 'results') else len(results)
            self.logger.debug(f"🔍 Found {count} relevant decisions")
            return results
        except Exception as e:
            self.logger.error(f"Failed to query decisions: {e}")
            return []

    # =========================================================================
    # User Preferences Memory - User preferences and styles
    # =========================================================================

    @property
    def preferences_memory(self) -> ChromaDBVectorMemory:
        """Get or create preferences memory store"""
        if self._preferences_memory is None:
            self._preferences_memory = self._create_memory_store("preferences")
        return self._preferences_memory

    async def add_preference(
            self,
            preference: str,
            category: str = "general",
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a user preference to memory

        Args:
            preference: The preference statement
            category: Category (code_style, framework, tool, etc.)
            metadata: Additional metadata
        """
        try:
            mem_metadata = metadata or {}
            mem_metadata.update({
                "type": "preference",
                "category": category
            })

            await self.preferences_memory.add(
                MemoryContent(
                    content=preference,
                    mime_type=MemoryMimeType.TEXT,
                    metadata=mem_metadata
                )
            )

            self.logger.debug(f"⚙️ Preference added: {category}")

        except Exception as e:
            self.logger.error(f"Failed to add preference: {e}")

    async def query_preferences(self, query: str) -> List[MemoryContent]:
        """Query preferences memory for relevant preferences"""
        try:
            results = await self.preferences_memory.query(query)
            count = len(results.results) if hasattr(results, 'results') else len(results)
            self.logger.debug(f"🔍 Found {count} relevant preferences")
            return results
        except Exception as e:
            self.logger.error(f"Failed to query preferences: {e}")
            return []

    # =========================================================================
    # User Memory - Information about the user
    # =========================================================================

    @property
    def user_memory(self) -> ChromaDBVectorMemory:
        """Get or create user memory store"""
        if self._user_memory is None:
            self._user_memory = self._create_memory_store("user_info")
        return self._user_memory

    async def add_user_info(
            self,
            info: str,
            category: str = "general",
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add user information to memory

        Args:
            info: Information about the user
            category: Category (personal, expertise, project, goal, etc.)
            metadata: Additional metadata
        """
        try:
            mem_metadata = metadata or {}
            mem_metadata.update({
                "type": "user_info",
                "category": category
            })

            await self.user_memory.add(
                MemoryContent(
                    content=info,
                    mime_type=MemoryMimeType.TEXT,
                    metadata=mem_metadata
                )
            )

            self.logger.debug(f"👤 User info added: {category}")

        except Exception as e:
            self.logger.error(f"Failed to add user info: {e}")

    async def query_user_info(self, query: str) -> List[MemoryContent]:
        """Query user memory for relevant user information"""
        try:
            results = await self.user_memory.query(query)
            count = len(results.results) if hasattr(results, 'results') else len(results)
            self.logger.debug(f"🔍 Found {count} relevant user info")
            return results
        except Exception as e:
            self.logger.error(f"Failed to query user info: {e}")
            return []

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
        }
        return language_map.get(ext, "unknown")

    async def clear_all(self) -> None:
        """Clear all memory stores"""
        try:
            if self._conversation_memory:
                await self._conversation_memory.clear()
                self.logger.info("🗑️ Conversation memory cleared")

            if self._codebase_memory:
                await self._codebase_memory.clear()
                self.logger.info("🗑️ Codebase memory cleared")

            if self._decision_memory:
                await self._decision_memory.clear()
                self.logger.info("🗑️ Decision memory cleared")

            if self._preferences_memory:
                await self._preferences_memory.clear()
                self.logger.info("🗑️ Preferences memory cleared")

            if self._user_memory:
                await self._user_memory.clear()
                self.logger.info("🗑️ User memory cleared")

        except Exception as e:
            self.logger.error(f"Failed to clear memory: {e}")

    async def close(self) -> None:
        """Close all memory stores"""
        try:
            if self._conversation_memory:
                await self._conversation_memory.close()

            if self._codebase_memory:
                await self._codebase_memory.close()

            if self._decision_memory:
                await self._decision_memory.close()

            if self._preferences_memory:
                await self._preferences_memory.close()

            if self._user_memory:
                await self._user_memory.close()

            self.logger.info("📚 Memory manager closed")

        except Exception as e:
            self.logger.error(f"Failed to close memory: {e}")
