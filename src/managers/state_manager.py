"""
State Manager - Gestión de estado usando save_state/load_state de AutoGen

Integra el sistema oficial de AutoGen para persistir estado de agentes y teams
con el sistema de memoria vectorial de ChromaDB.
"""
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging


class StateManager:
    """
    Gestor de estado que combina:
    1. save_state/load_state de AutoGen (oficial)
    2. Memoria vectorial de ChromaDB
    3. Auto-save periódico

    Esto permite:
    - Recuperar conversaciones completas entre sesiones
    - Mantener el contexto de los agentes intacto
    - Búsqueda semántica en conversaciones pasadas
    """

    def __init__(
        self,
        state_dir: Optional[Path] = None,
        auto_save_enabled: bool = True,
        auto_save_interval: int = 300,  # 5 minutos
    ):
        """
        Initialize State Manager

        Args:
            state_dir: Directory to store state files (defaults to ~/.daveagent/state)
            auto_save_enabled: Enable automatic periodic state saving
            auto_save_interval: Auto-save interval in seconds
        """
        self.logger = logging.getLogger(__name__)

        # Set up state directory
        if state_dir is None:
            home = Path.home()
            state_dir = home / ".daveagent" / "state"

        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.auto_save_enabled = auto_save_enabled
        self.auto_save_interval = auto_save_interval
        self._auto_save_task: Optional[asyncio.Task] = None

        # Track current session
        self.session_id: Optional[str] = None
        self.last_save_time: Optional[datetime] = None

        # State cache
        self._agent_states: Dict[str, Dict] = {}
        self._team_states: Dict[str, Dict] = {}

        self.logger.info(f"💾 StateManager initialized: {self.state_dir}")

    # =========================================================================
    # Session Management
    # =========================================================================

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new session or resume existing one

        Args:
            session_id: Session ID to resume, or None for new session

        Returns:
            Session ID
        """
        if session_id is None:
            # Generate new session ID
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.session_id = session_id
        self.logger.info(f"📝 Session started: {session_id}")

        # Start auto-save if enabled
        if self.auto_save_enabled and self._auto_save_task is None:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

        return session_id

    def get_session_path(self, session_id: Optional[str] = None) -> Path:
        """Get path to session state file"""
        session_id = session_id or self.session_id or "default"
        return self.state_dir / f"session_{session_id}.json"

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions

        Returns:
            List of session info dicts
        """
        sessions = []

        for state_file in self.state_dir.glob("session_*.json"):
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)

                sessions.append({
                    "session_id": data.get("session_id"),
                    "saved_at": data.get("saved_at"),
                    "num_agents": len(data.get("agent_states", {})),
                    "num_teams": len(data.get("team_states", {})),
                    "file_path": str(state_file)
                })

            except Exception as e:
                self.logger.warning(f"Failed to read session {state_file}: {e}")

        # Sort by saved_at descending
        sessions.sort(key=lambda x: x.get("saved_at", ""), reverse=True)

        return sessions

    # =========================================================================
    # Agent State Management
    # =========================================================================

    async def save_agent_state(
        self,
        agent_name: str,
        agent: Any,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save state of a single agent

        Args:
            agent_name: Name/identifier for the agent
            agent: Agent instance (must have save_state method)
            metadata: Additional metadata to store
        """
        try:
            # Call AutoGen's save_state
            agent_state = await agent.save_state()

            # Store with metadata
            self._agent_states[agent_name] = {
                "state": agent_state,
                "metadata": metadata or {},
                "saved_at": datetime.now().isoformat()
            }

            self.logger.debug(f"💾 Agent state saved: {agent_name}")

        except Exception as e:
            self.logger.error(f"Failed to save agent state {agent_name}: {e}")
            raise

    async def load_agent_state(
        self,
        agent_name: str,
        agent: Any
    ) -> bool:
        """
        Load state into an agent

        Args:
            agent_name: Name/identifier for the agent
            agent: Agent instance (must have load_state method)

        Returns:
            True if state was loaded, False if no state found
        """
        try:
            if agent_name not in self._agent_states:
                self.logger.warning(f"No state found for agent: {agent_name}")
                return False

            agent_data = self._agent_states[agent_name]
            agent_state = agent_data["state"]

            # Call AutoGen's load_state
            await agent.load_state(agent_state)

            self.logger.debug(f"📂 Agent state loaded: {agent_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load agent state {agent_name}: {e}")
            raise

    # =========================================================================
    # Team State Management
    # =========================================================================

    async def save_team_state(
        self,
        team_name: str,
        team: Any,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save state of a team (includes all agents in the team)

        Args:
            team_name: Name/identifier for the team
            team: Team instance (must have save_state method)
            metadata: Additional metadata to store
        """
        try:
            # Call AutoGen's save_state on team
            team_state = await team.save_state()

            # Store with metadata
            self._team_states[team_name] = {
                "state": team_state,
                "metadata": metadata or {},
                "saved_at": datetime.now().isoformat()
            }

            self.logger.debug(f"💾 Team state saved: {team_name}")

        except Exception as e:
            self.logger.error(f"Failed to save team state {team_name}: {e}")
            raise

    async def load_team_state(
        self,
        team_name: str,
        team: Any
    ) -> bool:
        """
        Load state into a team

        Args:
            team_name: Name/identifier for the team
            team: Team instance (must have load_state method)

        Returns:
            True if state was loaded, False if no state found
        """
        try:
            if team_name not in self._team_states:
                self.logger.warning(f"No state found for team: {team_name}")
                return False

            team_data = self._team_states[team_name]
            team_state = team_data["state"]

            # Call AutoGen's load_state
            await team.load_state(team_state)

            self.logger.debug(f"📂 Team state loaded: {team_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load team state {team_name}: {e}")
            raise

    # =========================================================================
    # Persistence (Save/Load to Disk)
    # =========================================================================

    async def save_to_disk(
        self,
        session_id: Optional[str] = None,
        include_metadata: bool = True
    ) -> Path:
        """
        Save all cached states to disk

        Args:
            session_id: Session ID (defaults to current session)
            include_metadata: Include additional metadata

        Returns:
            Path to saved state file
        """
        session_id = session_id or self.session_id or "default"
        state_path = self.get_session_path(session_id)

        try:
            # Prepare data
            data = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "agent_states": self._agent_states,
                "team_states": self._team_states,
            }

            if include_metadata:
                data["metadata"] = {
                    "auto_save_enabled": self.auto_save_enabled,
                    "auto_save_interval": self.auto_save_interval,
                }

            # Write to file
            with open(state_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            self.last_save_time = datetime.now()
            self.logger.info(f"💾 State saved to: {state_path}")

            return state_path

        except Exception as e:
            self.logger.error(f"Failed to save state to disk: {e}")
            raise

    async def load_from_disk(
        self,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Load states from disk

        Args:
            session_id: Session ID to load (defaults to current session)

        Returns:
            True if state was loaded, False if no state found
        """
        session_id = session_id or self.session_id or "default"
        state_path = self.get_session_path(session_id)

        if not state_path.exists():
            self.logger.warning(f"No state file found: {state_path}")
            return False

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            self._agent_states = data.get("agent_states", {})
            self._team_states = data.get("team_states", {})
            self.session_id = data.get("session_id", session_id)

            self.logger.info(
                f"📂 State loaded from: {state_path} "
                f"({len(self._agent_states)} agents, {len(self._team_states)} teams)"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to load state from disk: {e}")
            raise

    # =========================================================================
    # Auto-Save
    # =========================================================================

    async def _auto_save_loop(self):
        """Background task that auto-saves state periodically"""
        self.logger.info(
            f"🔄 Auto-save enabled: every {self.auto_save_interval}s"
        )

        while self.auto_save_enabled:
            try:
                await asyncio.sleep(self.auto_save_interval)

                # Only save if we have states
                if self._agent_states or self._team_states:
                    await self.save_to_disk()
                    self.logger.debug("🔄 Auto-save completed")

            except asyncio.CancelledError:
                self.logger.info("🔄 Auto-save cancelled")
                break

            except Exception as e:
                self.logger.error(f"Auto-save error: {e}")
                # Continue despite errors

    def enable_auto_save(self, interval: Optional[int] = None):
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

        self.logger.info(f"🔄 Auto-save enabled: {self.auto_save_interval}s")

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
        """Close state manager and save final state"""
        try:
            # Stop auto-save
            if self._auto_save_task:
                self._auto_save_task.cancel()
                try:
                    await self._auto_save_task
                except asyncio.CancelledError:
                    pass

            # Final save
            if self._agent_states or self._team_states:
                await self.save_to_disk()

            self.logger.info("💾 StateManager closed")

        except Exception as e:
            self.logger.error(f"Error closing StateManager: {e}")

    def clear_cache(self):
        """Clear in-memory state cache"""
        self._agent_states = {}
        self._team_states = {}
        self.logger.info("🗑️ State cache cleared")

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

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get state manager statistics"""
        return {
            "session_id": self.session_id,
            "state_dir": str(self.state_dir),
            "num_agents": len(self._agent_states),
            "num_teams": len(self._team_states),
            "auto_save_enabled": self.auto_save_enabled,
            "auto_save_interval": self.auto_save_interval,
            "last_save_time": self.last_save_time.isoformat() if self.last_save_time else None,
        }
