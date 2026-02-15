"""
State Manager - State management using AutoGen's save_state/load_state

Saves and loads the main_team state as a single JSON file.
Session metadata is stored separately under .daveagent/state/.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


class StateManager:
    """
    State manager that:
    1. Saves/loads the AutoGen team state as a single JSON file
    2. Manages session metadata
    3. Periodic auto-save
    """

    def __init__(
        self,
        state_dir: Path | None = None,
        auto_save_enabled: bool = True,
        auto_save_interval: int = 300,  # 5 minutos
    ):
        """
        Initialize State Manager

        Args:
            state_dir: Directory to store session metadata files (defaults to .daveagent/state)
            auto_save_enabled: Enable automatic periodic state saving
            auto_save_interval: Auto-save interval in seconds
        """
        self.logger = logging.getLogger(__name__)

        # Set up state directory (workspace-relative, like logs and conversations)
        if state_dir is None:
            state_dir = Path(".daveagent") / "state"

        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.auto_save_enabled = auto_save_enabled
        self.auto_save_interval = auto_save_interval
        self._auto_save_task: asyncio.Task | None = None

        # Track current session
        self.session_id: str | None = None
        self.last_save_time: datetime | None = None
        self.session_metadata: dict[str, Any] = {}

    # =========================================================================
    # Session Management
    # =========================================================================

    def start_session(
        self,
        session_id: str | None = None,
        title: str | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
    ) -> str:
        """
        Start a new session or resume existing one

        Args:
            session_id: Session ID to resume, or None for new session
            title: Descriptive title for the session
            tags: List of tags for categorization
            description: Session description

        Returns:
            Session ID
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.session_id = session_id

        self.session_metadata = {
            "title": title or "Untitled Session",
            "tags": tags or [],
            "description": description or "",
            "created_at": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
        }

        if self.auto_save_enabled and self._auto_save_task is None:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

        return session_id

    def get_session_path(self, session_id: str | None = None) -> Path:
        """Get path to session metadata file"""
        session_id = session_id or self.session_id or "default"
        return self.state_dir / f"session_{session_id}.json"

    def list_sessions(self) -> list[dict[str, Any]]:
        """
        List all available sessions with metadata

        Returns:
            List of session info dicts
        """
        sessions = []

        for state_file in self.state_dir.glob("session_*.json"):
            try:
                with open(state_file) as f:
                    data = json.load(f)

                metadata = data.get("session_metadata", {})

                sessions.append(
                    {
                        "session_id": data.get("session_id"),
                        "title": metadata.get("title", "Untitled"),
                        "description": metadata.get("description", ""),
                        "tags": metadata.get("tags", []),
                        "created_at": metadata.get("created_at"),
                        "saved_at": data.get("saved_at"),
                        "last_interaction": metadata.get("last_interaction"),
                        "file_path": str(state_file),
                    }
                )

            except Exception as e:
                self.logger.warning(f"Failed to read session {state_file}: {e}")

        sessions.sort(key=lambda x: x.get("last_interaction") or "", reverse=True)

        return sessions

    # =========================================================================
    # Team State Management
    # =========================================================================

    async def save_team_state(self, team: Any) -> Path:
        """
        Save the main_team state to .daveagent/agent_state.json

        Args:
            team: The AutoGen team instance (must have save_state method)

        Returns:
            Path to the saved state file
        """
        state_file = self.state_dir.parent / "agent_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        team_state = await team.save_state()

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(team_state, f, indent=2, ensure_ascii=False)

        self.logger.info(f"💾 Team state saved to {state_file}")
        return state_file

    async def load_team_state(self, team: Any) -> bool:
        """
        Load the main_team state from .daveagent/agent_state.json.
        Truncates message history to 150 messages to prevent token overflow.

        Args:
            team: The AutoGen team instance (must have load_state method)

        Returns:
            True if state was loaded, False if no state file found
        """
        state_file = self.state_dir.parent / "agent_state.json"

        if not state_file.exists():
            self.logger.info("No saved team state found")
            return False

        with open(state_file, "r", encoding="utf-8") as f:
            team_state = json.load(f)

        # Truncate message history to prevent token overflow
        if "message_thread" in team_state and isinstance(team_state["message_thread"], list):
            original_count = len(team_state["message_thread"])
            if original_count > 150:
                team_state["message_thread"] = team_state["message_thread"][-150:]
                self.logger.warning(
                    f"⚠️ Truncated message history from {original_count} to 150 messages to prevent token overflow"
                )
            else:
                self.logger.info(f"Loading {original_count} messages from saved state")

        await team.load_state(team_state)

        self.logger.info(f"📂 Team state loaded from {state_file}")
        return True

    # =========================================================================
    # Persistence (Session Metadata Save/Load to Disk)
    # =========================================================================

    async def save_to_disk(
        self, session_id: str | None = None, include_metadata: bool = True
    ) -> Path:
        """
        Save session metadata to disk

        Args:
            session_id: Session ID (defaults to current session)
            include_metadata: Include additional metadata

        Returns:
            Path to saved session file
        """
        session_id = session_id or self.session_id or "default"
        state_path = self.get_session_path(session_id)

        try:
            if self.session_metadata:
                self.session_metadata["last_interaction"] = datetime.now().isoformat()

            data = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "session_metadata": self.session_metadata,
            }

            if include_metadata:
                data["metadata"] = {
                    "auto_save_enabled": self.auto_save_enabled,
                    "auto_save_interval": self.auto_save_interval,
                }

            with open(state_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            self.last_save_time = datetime.now()
            self.logger.info(f"💾 Session metadata saved to: {state_path}")

            return state_path

        except Exception as e:
            self.logger.error(f"Failed to save session metadata to disk: {e}")
            raise

    async def load_from_disk(self, session_id: str | None = None) -> bool:
        """
        Load session metadata from disk

        Args:
            session_id: Session ID to load (defaults to current session)

        Returns:
            True if metadata was loaded, False if no file found
        """
        session_id = session_id or self.session_id or "default"
        state_path = self.get_session_path(session_id)

        if not state_path.exists():
            self.logger.warning(f"No session file found: {state_path}")
            return False

        try:
            with open(state_path) as f:
                data = json.load(f)

            self.session_id = data.get("session_id", session_id)
            self.session_metadata = data.get("session_metadata", {})

            self.logger.info(f"📂 Session metadata loaded from: {state_path}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to load session metadata from disk: {e}")
            raise

    # =========================================================================
    # Auto-Save
    # =========================================================================

    async def _auto_save_loop(self):
        """Background task that auto-saves session metadata periodically"""

        while self.auto_save_enabled:
            try:
                await asyncio.sleep(self.auto_save_interval)

                if self.session_id:
                    await self.save_to_disk()
                    self.logger.debug("🔄 Auto-save completed")

            except asyncio.CancelledError:
                self.logger.info("🔄 Auto-save cancelled")
                break

            except Exception as e:
                self.logger.error(f"Auto-save error: {e}")

    def enable_auto_save(self, interval: int | None = None):
        """
        Enable auto-save

        Args:
            interval: Save interval in seconds (None = use current)
        """
        if interval:
            self.auto_save_interval = interval

        self.auto_save_enabled = True

        if self._auto_save_task is None or self._auto_save_task.done():
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

    def disable_auto_save(self):
        """Disable auto-save"""
        self.auto_save_enabled = False

        if self._auto_save_task and not self._auto_save_task.done():
            self._auto_save_task.cancel()

        self.logger.info("🔄 Auto-save disabled")

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def close(self):
        """Close state manager and save final session metadata"""
        try:
            if self._auto_save_task:
                self._auto_save_task.cancel()
                try:
                    await self._auto_save_task
                except asyncio.CancelledError:
                    pass

            if self.session_id:
                await self.save_to_disk()

            self.logger.info("💾 StateManager closed")

        except Exception as e:
            self.logger.error(f"Error closing StateManager: {e}")

    def clear_current_session(self):
        """
        Clear the current session metadata.

        This is useful when reinitializing agents (e.g., changing modes).
        """
        self.session_metadata = {}
        self.logger.info(f"🧹 Current session cleared: {self.session_id}")

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from disk

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            state_path = self.get_session_path(session_id)

            if state_path.exists():
                state_path.unlink()
                self.logger.info(f"🗑️ Session deleted: {session_id}")
                return True
            else:
                self.logger.warning(f"Session not found: {session_id}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            raise

    def get_session_history(self, session_id: str | None = None) -> list[dict[str, Any]]:  # noqa: ARG002
        """
        Returns empty list — conversation history is now stored in the team state file,
        not in the session metadata JSON.
        """
        return []

    def get_session_metadata(self, session_id: str | None = None) -> dict[str, Any]:
        """
        Get metadata for a session

        Args:
            session_id: Session ID (defaults to current)

        Returns:
            Session metadata dict
        """
        try:
            if session_id is None or session_id == self.session_id:
                return self.session_metadata.copy()

            state_path = self.get_session_path(session_id)
            if not state_path.exists():
                return {}

            with open(state_path) as f:
                data = json.load(f)

            return data.get("session_metadata", {})

        except Exception as e:
            self.logger.error(f"Failed to get session metadata: {e}")
            return {}

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_statistics(self) -> dict[str, Any]:
        """Get state manager statistics"""
        return {
            "session_id": self.session_id,
            "state_dir": str(self.state_dir),
            "auto_save_enabled": self.auto_save_enabled,
            "auto_save_interval": self.auto_save_interval,
            "last_save_time": self.last_save_time.isoformat() if self.last_save_time else None,
        }
