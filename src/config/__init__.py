"""
System configuration
"""

from src.config.prompts import (
    AGENT_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    CODER_AGENT_DESCRIPTION,
    COMPLEXITY_DETECTOR_PROMPT,
    TASK_PLANNER_DESCRIPTION,
    TASK_PLANNER_SYSTEM_MESSAGE,
    TASK_PLANNER_UPDATER_MESSAGE,
    PLANNING_AGENT_DESCRIPTION,
    PLANNING_AGENT_SYSTEM_MESSAGE,
)
from src.config.settings import DaveAgentSettings, get_settings
from src.config.constants import (
    DAVEAGENT_VERSION,
    DAVEAGENT_NAME,
    is_telemetry_enabled,
    set_telemetry_enabled,
    setup_langfuse_environment,
)

__all__ = [
    "AGENT_SYSTEM_PROMPT",
    "CHAT_SYSTEM_PROMPT",
    "DaveAgentSettings",
    "get_settings",
    "CODER_AGENT_DESCRIPTION",
    "TASK_PLANNER_DESCRIPTION",
    "TASK_PLANNER_SYSTEM_MESSAGE",
    "TASK_PLANNER_UPDATER_MESSAGE",
    "COMPLEXITY_DETECTOR_PROMPT",
    "PLANNING_AGENT_DESCRIPTION",
    "PLANNING_AGENT_SYSTEM_MESSAGE",
    "DAVEAGENT_VERSION",
    "DAVEAGENT_NAME",
    "is_telemetry_enabled",
    "set_telemetry_enabled",
    "setup_langfuse_environment",
]
