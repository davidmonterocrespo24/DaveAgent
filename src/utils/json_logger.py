"""
JSON Logger - Complete logging system to capture all interactions

Records in JSON:
- User input
- Messages between agents
- Tool calls (with arguments)
- Tool results
- LLM responses
- Router decisions
- Thought events (ThoughtEvent)
- Errors and exceptions

This provides complete system traceability independent of Langfuse.
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class JSONLogger:
    """
    Dedicated logger to capture all system interactions in JSON.

    Each session creates a JSON file with:
    - Session metadata
    - Complete list of chronological events
    - Statistics summary
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize JSON Logger

        Args:
            log_dir: Directory to store JSON logs (defaults to ~/.daveagent/logs/json)
        """
        self.logger = logging.getLogger(__name__)

        # Set up log directory
        if log_dir is None:
            home = Path.home()
            log_dir = home / ".daveagent" / "logs" / "json"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current session state
        self.session_id: Optional[str] = None
        self.session_start: Optional[datetime] = None
        self.events: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.stats: Dict[str, int] = {
            "user_messages": 0,
            "agent_messages": 0,
            "tool_calls": 0,
            "thoughts": 0,
            "errors": 0,
        }

        self.logger.info(f"📝 JSONLogger initialized: {self.log_dir}")

    def start_session(self, session_id: Optional[str] = None, mode: str = "agent", **kwargs):
        """
        Start a new logging session

        Args:
            session_id: Session ID (defaults to timestamp)
            mode: Current mode (agent/chat)
            **kwargs: Additional metadata
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.session_id = session_id
        self.session_start = datetime.now()
        self.events = []
        self.stats = {
            "user_messages": 0,
            "agent_messages": 0,
            "tool_calls": 0,
            "thoughts": 0,
            "errors": 0,
        }

        self.metadata = {
            "session_id": session_id,
            "start_time": self.session_start.isoformat(),
            "mode": mode,
            **kwargs,
        }

        self.logger.info(f"📝 Started JSON logging session: {session_id}")

    def log_user_message(self, content: str, mentioned_files: Optional[List[str]] = None):
        """Log user input"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "user_message",
            "content": content,
            "mentioned_files": mentioned_files or [],
        }
        self.events.append(event)
        self.stats["user_messages"] += 1
        self.logger.debug(f"📝 Logged user message: {content[:50]}...")

    def log_agent_message(self, agent_name: str, content: str, message_type: str = "text"):
        """Log agent response"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "agent_message",
            "agent_name": agent_name,
            "message_type": message_type,
            "content": content,
        }
        self.events.append(event)
        self.stats["agent_messages"] += 1
        self.logger.debug(f"📝 Logged agent message: {agent_name} - {content[:50]}...")

    def log_thought(self, agent_name: str, thought: str):
        """Log agent thought/reasoning"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "thought",
            "agent_name": agent_name,
            "content": thought,
        }
        self.events.append(event)
        self.stats["thoughts"] += 1
        self.logger.debug(f"📝 Logged thought: {agent_name} - {thought[:50]}...")

    def log_tool_call(self, agent_name: str, tool_name: str, arguments: Dict[str, Any]):
        """Log tool call with arguments"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "tool_call",
            "agent_name": agent_name,
            "tool_name": tool_name,
            "arguments": arguments,
        }
        self.events.append(event)
        self.stats["tool_calls"] += 1
        self.logger.debug(f"📝 Logged tool call: {tool_name}")

    def log_tool_result(self, agent_name: str, tool_name: str, result: Any, success: bool = True):
        """Log tool execution result"""
        # Convert result to string if it's too large
        if isinstance(result, str) and len(result) > 1000:
            result_preview = result[:1000] + "... (truncated)"
        else:
            result_preview = result

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "tool_result",
            "agent_name": agent_name,
            "tool_name": tool_name,
            "success": success,
            "result": str(result_preview),
        }
        self.events.append(event)
        self.logger.debug(
            f"📝 Logged tool result: {tool_name} - {'success' if success else 'failed'}"
        )

    def log_router_decision(self, selected_agent: str, reason: Optional[str] = None):
        """Log router's agent selection decision"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "router_decision",
            "selected_agent": selected_agent,
            "reason": reason,
        }
        self.events.append(event)
        self.logger.debug(f"📝 Logged router decision: {selected_agent}")

    def log_error(self, error: Exception, context: str = ""):
        """Log error with full traceback"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc(),
        }
        self.events.append(event)
        self.stats["errors"] += 1
        self.logger.error(f"📝 Logged error: {error}")

    def log_llm_call(
        self,
        agent_name: str,
        messages: List[Dict[str, Any]],
        response: Optional[str] = None,
        model: Optional[str] = None,
        tokens_used: Optional[Dict[str, int]] = None,
    ):
        """
        Log complete LLM call (input and output)

        Args:
            agent_name: Name of the agent making the call
            messages: Input messages to LLM
            response: LLM response
            model: Model name
            tokens_used: Token usage stats
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "llm_call",
            "agent_name": agent_name,
            "model": model,
            "input_messages": messages,
            "response": response,
            "tokens_used": tokens_used or {},
        }
        self.events.append(event)
        self.logger.debug(f"📝 Logged LLM call: {agent_name} - {len(messages)} messages")

    def end_session(self, summary: Optional[str] = None):
        """End session and save to file"""
        if not self.session_id:
            self.logger.warning("No active session to end")
            return

        session_end = datetime.now()
        duration = (session_end - self.session_start).total_seconds()

        # Build final JSON structure
        log_data = {
            "metadata": {
                **self.metadata,
                "end_time": session_end.isoformat(),
                "duration_seconds": duration,
                "summary": summary,
            },
            "statistics": self.stats,
            "events": self.events,
        }

        # Save to file
        filename = f"session_{self.session_id}.json"
        filepath = self.log_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"📝 JSON log saved: {filepath}")
            self.logger.info(f"   Events: {len(self.events)}, Duration: {duration:.1f}s")
            self.logger.info(f"   Stats: {self.stats}")

            # Count LLM calls in events
            llm_calls = sum(1 for e in self.events if e.get("event_type") == "llm_call")
            if llm_calls > 0:
                self.logger.info(f"   🤖 LLM calls logged: {llm_calls}")

        except Exception as e:
            self.logger.error(f"Error saving JSON log: {e}")

    def get_session_filepath(self) -> Optional[Path]:
        """Get filepath for current session"""
        if not self.session_id:
            return None
        return self.log_dir / f"session_{self.session_id}.json"
