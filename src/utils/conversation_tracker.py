"""
Conversation Tracker - Tracks all LLM interactions in JSON format
Stores in .daveagent/conversations.json with newest first
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class ConversationTracker:
    """Tracks all LLM conversations in JSON format"""

    def __init__(self, data_dir: str = ".daveagent"):
        """
        Initialize conversation tracker

        Args:
            data_dir: Directory to store conversation data
        """
        self.data_dir = Path(data_dir)
        self.conversations_file = self.data_dir / "conversations.json"

        # Create directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)

        # Initialize conversations file if it doesn't exist
        if not self.conversations_file.exists():
            self._save_conversations([])

    def _load_conversations(self) -> List[Dict[str, Any]]:
        """Load conversations from JSON file"""
        try:
            with open(self.conversations_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_conversations(self, conversations: List[Dict[str, Any]]):
        """Save conversations to JSON file"""
        with open(self.conversations_file, "w", encoding="utf-8") as f:
            json.dump(conversations, f, indent=2, ensure_ascii=False)

    def log_interaction(
        self,
        user_request: str,
        agent_response: str,
        model: str,
        provider: str,
        *,
        agent_name: str = "DaveAgent",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an LLM interaction

        Args:
            user_request: User's request/query
            agent_response: Agent's response
            model: Model name (e.g., "deepseek-chat")
            provider: Provider name (e.g., "DeepSeek", "OpenAI")
            agent_name: Name of the agent that responded
            metadata: Additional metadata (tokens, tools used, etc.)

        Returns:
            Conversation ID
        """
        # Load existing conversations
        conversations = self._load_conversations()

        # Create conversation record
        conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        conversation = {
            "id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "agent": agent_name,
            "model": model,
            "provider": provider,
            "user_request": user_request,
            "agent_response": agent_response,
            "metadata": metadata or {},
        }

        # Add to beginning (newest first)
        conversations.insert(0, conversation)

        # Save back to file
        self._save_conversations(conversations)

        return conversation_id

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversations

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of recent conversations (newest first)
        """
        conversations = self._load_conversations()
        return conversations[:limit]

    def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific conversation by ID

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation record or None if not found
        """
        conversations = self._load_conversations()
        for conv in conversations:
            if conv.get("id") == conversation_id:
                return conv
        return None

    def get_conversations_by_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Get all conversations from a specific date

        Args:
            date: Date in format "YYYY-MM-DD"

        Returns:
            List of conversations from that date
        """
        conversations = self._load_conversations()
        return [conv for conv in conversations if conv.get("date") == date]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about conversations

        Returns:
            Dictionary with statistics
        """
        conversations = self._load_conversations()

        if not conversations:
            return {
                "total_conversations": 0,
                "models_used": {},
                "providers_used": {},
                "conversations_by_date": {},
            }

        # Count by model
        models: Dict[str, int] = {}
        for conv in conversations:
            model = conv.get("model", "unknown")
            models[model] = models.get(model, 0) + 1

        # Count by provider
        providers: Dict[str, int] = {}
        for conv in conversations:
            provider = conv.get("provider", "unknown")
            providers[provider] = providers.get(provider, 0) + 1

        # Count by date
        by_date: Dict[str, int] = {}
        for conv in conversations:
            date = conv.get("date", "unknown")
            by_date[date] = by_date.get(date, 0) + 1

        return {
            "total_conversations": len(conversations),
            "models_used": models,
            "providers_used": providers,
            "conversations_by_date": by_date,
            "oldest_conversation": conversations[-1].get("timestamp") if conversations else None,
            "newest_conversation": conversations[0].get("timestamp") if conversations else None,
        }

    def clear_old_conversations(self, days: int = 30):
        """
        Clear conversations older than specified days

        Args:
            days: Number of days to keep
        """
        from datetime import timedelta

        conversations = self._load_conversations()
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter conversations
        filtered = [
            conv
            for conv in conversations
            if datetime.fromisoformat(conv.get("timestamp", "")) > cutoff_date
        ]

        self._save_conversations(filtered)

        return len(conversations) - len(filtered)  # Number removed


# Global instance
_tracker_instance: Optional[ConversationTracker] = None


def get_conversation_tracker(data_dir: str = ".daveagent") -> ConversationTracker:
    """Get or create global conversation tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ConversationTracker(data_dir)
    return _tracker_instance
