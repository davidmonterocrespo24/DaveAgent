"""
State Manager - State management using AutoGen's save_state/load_state

Integrates the official AutoGen system to persist agent and team state
with the ChromaDB vector memory system.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


class StateManager:
    """
    State manager that combines:
    1. AutoGen's save_state/load_state (official)
    2. ChromaDB vector memory
    3. Periodic auto-save

    This allows:
    - Recovering complete conversations between sessions
    - Keeping agent context intact
    - Semantic search in past conversations
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
            state_dir: Directory to store state files (defaults to .daveagent/state in workspace)
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

        # State cache
        self._agent_states: dict[str, dict] = {}
        self._team_states: dict[str, dict] = {}

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
            # Generate new session ID
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.session_id = session_id

        # Store session metadata
        self.session_metadata = {
            "title": title or "Untitled Session",
            "tags": tags or [],
            "description": description or "",
            "created_at": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
        }

        # Start auto-save if enabled
        if self.auto_save_enabled and self._auto_save_task is None:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

        return session_id

    def get_session_path(self, session_id: str | None = None) -> Path:
        """Get path to session state file"""
        session_id = session_id or self.session_id or "default"
        return self.state_dir / f"session_{session_id}.json"

    def list_sessions(self) -> list[dict[str, Any]]:
        """
        List all available sessions with enhanced metadata

        Returns:
            List of session info dicts with metadata
        """
        sessions = []

        for state_file in self.state_dir.glob("session_*.json"):
            try:
                with open(state_file) as f:
                    data = json.load(f)

                # Extract session metadata
                metadata = data.get("session_metadata", {})

                # Count total messages in all agents
                total_messages = 0
                agent_states = data.get("agent_states", {})
                for agent_data in agent_states.values():
                    state = agent_data.get("state", {})
                    llm_context = state.get("llm_context", {})
                    messages = llm_context.get("messages", [])
                    total_messages += len(messages)

                sessions.append(
                    {
                        "session_id": data.get("session_id"),
                        "title": metadata.get("title", "Untitled"),
                        "description": metadata.get("description", ""),
                        "tags": metadata.get("tags", []),
                        "created_at": metadata.get("created_at"),
                        "saved_at": data.get("saved_at"),
                        "last_interaction": metadata.get("last_interaction"),
                        "num_agents": len(data.get("agent_states", {})),
                        "num_teams": len(data.get("team_states", {})),
                        "total_messages": total_messages,
                        "file_path": str(state_file),
                    }
                )

            except Exception as e:
                self.logger.warning(f"Failed to read session {state_file}: {e}")

        # Sort by last_interaction descending (handle None values)
        sessions.sort(key=lambda x: x.get("last_interaction") or "", reverse=True)

        return sessions

    # =========================================================================
    # Agent State Management
    # =========================================================================

    async def save_agent_state(
        self, agent_name: str, agent: Any, metadata: dict | None = None
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
                "saved_at": datetime.now().isoformat(),
            }

            self.logger.debug(f"💾 Agent state saved: {agent_name}")

        except Exception as e:
            self.logger.error(f"Failed to save agent state {agent_name}: {e}")
            raise

    async def load_agent_state(self, agent_name: str, agent: Any) -> bool:
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
        self, team_name: str, team: Any, metadata: dict | None = None
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
                "saved_at": datetime.now().isoformat(),
            }

            self.logger.debug(f"💾 Team state saved: {team_name}")

        except Exception as e:
            self.logger.error(f"Failed to save team state {team_name}: {e}")
            raise

    async def load_team_state(self, team_name: str, team: Any) -> bool:
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
        self, session_id: str | None = None, include_metadata: bool = True
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
            # Update last interaction time
            if self.session_metadata:
                self.session_metadata["last_interaction"] = datetime.now().isoformat()

            # Prepare data
            data = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "session_metadata": self.session_metadata,
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

    async def load_from_disk(self, session_id: str | None = None) -> bool:
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
            with open(state_path) as f:
                data = json.load(f)

            self._agent_states = data.get("agent_states", {})
            self._team_states = data.get("team_states", {})
            self.session_id = data.get("session_id", session_id)
            self.session_metadata = data.get("session_metadata", {})

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

    def clear_current_session(self):
        """
        Clear the current session's agent states without losing session metadata.

        This is useful when reinitializing agents (e.g., changing modes) to avoid
        conflicts with multiple system messages in the conversation history.
        """
        self._agent_states = {}
        self._team_states = {}
        self.logger.info(f"🧹 Current session cleared: {self.session_id}")
        self.logger.debug("   Agent and team states reset (metadata preserved)")

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

    def get_session_history(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """
        Extract conversation history from current session

        Args:
            session_id: Session ID (defaults to current)

        Returns:
            List of messages in chronological order
        """
        try:
            # Use current session if none specified
            if session_id is None:
                # Use cached state
                agent_states = self._agent_states
            else:
                # Load from disk
                state_path = self.get_session_path(session_id)
                if not state_path.exists():
                    return []

                with open(state_path) as f:
                    data = json.load(f)
                agent_states = data.get("agent_states", {})

            # Extract all messages from all agents
            all_messages = []

            for agent_name, agent_data in agent_states.items():
                state = agent_data.get("state", {})
                llm_context = state.get("llm_context", {})
                messages = llm_context.get("messages", [])

                for msg in messages:
                    all_messages.append(
                        {
                            "agent": agent_name,
                            "source": msg.get("source", "unknown"),
                            "type": msg.get("type", "unknown"),
                            "content": msg.get("content", ""),
                            "thought": msg.get("thought"),
                        }
                    )

            return all_messages

        except Exception as e:
            self.logger.error(f"Failed to get session history: {e}")
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

            # Load from disk
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
    # Tool Reflection Analysis
    # =========================================================================

    def extract_tool_reflections(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """
        Extract all tool calls and their reflections from a session.

        This analyzes the saved state to extract:
        - Tool calls made by agents
        - Reasoning/thoughts before tool calls
        - Tool execution results
        - Success/failure status

        Args:
            session_id: Session ID to analyze (defaults to current)

        Returns:
            List of tool reflection dicts with structure:
            {
                "agent": str,
                "tool_name": str,
                "arguments": dict,
                "thought": str | None,
                "result": str | None,
                "is_error": bool,
                "timestamp_index": int
            }
        """
        try:
            # Load state
            if session_id is None:
                agent_states = self._agent_states
                team_states = self._team_states
            else:
                state_path = self.get_session_path(session_id)
                if not state_path.exists():
                    return []

                with open(state_path) as f:
                    data = json.load(f)
                agent_states = data.get("agent_states", {})
                team_states = data.get("team_states", {})

            reflections = []

            # Process team states (which contain agent messages)
            for team_name, team_data in team_states.items():
                team_state = team_data.get("state", {})
                agent_states_in_team = team_state.get("agent_states", {})

                for agent_key, agent_container in agent_states_in_team.items():
                    agent_name = agent_key.split("/")[0]

                    # Navigate to agent state
                    agent_state = agent_container.get("agent_state", {})
                    llm_messages = agent_state.get("llm_messages", [])

                    # Process messages
                    for i, msg in enumerate(llm_messages):
                        msg_type = msg.get("type")

                        if msg_type == "AssistantMessage":
                            content = msg.get("content")
                            thought = msg.get("thought")

                            # Check if this message contains tool calls
                            if isinstance(content, list):
                                for tool_call in content:
                                    if isinstance(tool_call, dict) and "name" in tool_call:
                                        tool_name = tool_call.get("name")
                                        tool_args = tool_call.get("arguments", {})

                                        # Parse arguments if JSON string
                                        if isinstance(tool_args, str):
                                            try:
                                                tool_args = json.loads(tool_args)
                                            except json.JSONDecodeError:
                                                pass

                                        # Look for result in next message
                                        result = None
                                        is_error = False
                                        if i + 1 < len(llm_messages):
                                            next_msg = llm_messages[i + 1]
                                            if next_msg.get("type") == "FunctionExecutionResultMessage":
                                                results = next_msg.get("content", [])
                                                for res in results:
                                                    if isinstance(res, dict):
                                                        result = res.get("content", "")
                                                        is_error = res.get("is_error", False)
                                                        break

                                        reflections.append({
                                            "agent": agent_name,
                                            "tool_name": tool_name,
                                            "arguments": tool_args if isinstance(tool_args, dict) else {},
                                            "thought": thought,
                                            "result": result,
                                            "is_error": is_error,
                                            "timestamp_index": i,
                                        })

            # Also process individual agent states (not in teams)
            for agent_name, agent_data in agent_states.items():
                state = agent_data.get("state", {})
                llm_context = state.get("llm_context", {})
                messages = llm_context.get("messages", [])

                for i, msg in enumerate(messages):
                    msg_type = msg.get("type")

                    if msg_type == "AssistantMessage":
                        content = msg.get("content")
                        thought = msg.get("thought")

                        if isinstance(content, list):
                            for tool_call in content:
                                if isinstance(tool_call, dict) and "name" in tool_call:
                                    tool_name = tool_call.get("name")
                                    tool_args = tool_call.get("arguments", {})

                                    # Parse arguments if JSON string
                                    if isinstance(tool_args, str):
                                        try:
                                            tool_args = json.loads(tool_args)
                                        except json.JSONDecodeError:
                                            pass

                                    # Look for result
                                    result = None
                                    is_error = False
                                    if i + 1 < len(messages):
                                        next_msg = messages[i + 1]
                                        if next_msg.get("type") == "FunctionExecutionResultMessage":
                                            results = next_msg.get("content", [])
                                            for res in results:
                                                if isinstance(res, dict):
                                                    result = res.get("content", "")
                                                    is_error = res.get("is_error", False)
                                                    break

                                    reflections.append({
                                        "agent": agent_name,
                                        "tool_name": tool_name,
                                        "arguments": tool_args if isinstance(tool_args, dict) else {},
                                        "thought": thought,
                                        "result": result,
                                        "is_error": is_error,
                                        "timestamp_index": i,
                                    })

            return reflections

        except Exception as e:
            self.logger.error(f"Failed to extract tool reflections: {e}")
            return []

    def get_tool_usage_stats(self, session_id: str | None = None) -> dict[str, Any]:
        """
        Get statistics about tool usage and reflection quality.

        Args:
            session_id: Session ID to analyze (defaults to current)

        Returns:
            Dictionary with tool usage statistics including:
            - total_tools_called: Total number of tool invocations
            - tools_with_reflection: Count of tools with reasoning
            - tools_without_reflection: Count without reasoning
            - reflection_rate: Percentage of tools with reflections
            - tool_frequency: Dict of tool names to call counts
            - error_rate: Percentage of failed tool calls
            - agents_using_tools: List of agents that used tools
        """
        reflections = self.extract_tool_reflections(session_id)

        if not reflections:
            return {
                "total_tools_called": 0,
                "tools_with_reflection": 0,
                "tools_without_reflection": 0,
                "reflection_rate": 0.0,
                "tool_frequency": {},
                "error_rate": 0.0,
                "agents_using_tools": [],
            }

        total = len(reflections)
        with_thought = sum(1 for r in reflections if r.get("thought"))
        without_thought = total - with_thought
        errors = sum(1 for r in reflections if r.get("is_error"))

        # Tool frequency
        tool_freq = {}
        for r in reflections:
            tool_name = r.get("tool_name", "unknown")
            tool_freq[tool_name] = tool_freq.get(tool_name, 0) + 1

        # Unique agents
        agents = list(set(r.get("agent", "unknown") for r in reflections))

        return {
            "total_tools_called": total,
            "tools_with_reflection": with_thought,
            "tools_without_reflection": without_thought,
            "reflection_rate": (with_thought / total * 100) if total > 0 else 0.0,
            "tool_frequency": tool_freq,
            "error_rate": (errors / total * 100) if total > 0 else 0.0,
            "agents_using_tools": agents,
        }

    def save_tool_reflection_report(
        self, session_id: str | None = None, output_path: Path | None = None
    ) -> Path:
        """
        Generate and save a detailed tool reflection report.

        Args:
            session_id: Session ID to analyze (defaults to current)
            output_path: Path to save report (defaults to state_dir/reflections/)

        Returns:
            Path to saved report file
        """
        session_id = session_id or self.session_id or "default"

        if output_path is None:
            reflections_dir = self.state_dir / "reflections"
            reflections_dir.mkdir(parents=True, exist_ok=True)
            output_path = reflections_dir / f"reflection_report_{session_id}.json"

        # Extract data
        reflections = self.extract_tool_reflections(session_id)
        stats = self.get_tool_usage_stats(session_id)

        # Build report
        report = {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "tool_reflections": reflections,
        }

        # Save report
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"📊 Tool reflection report saved to: {output_path}")
        return output_path

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_statistics(self) -> dict[str, Any]:
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