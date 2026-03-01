"""
AgentOrchestrator - Core agent initialization and management
Handles model clients, tools, agents, and team creation
"""

# IMPORTANTE: Filtros de warnings ANTES de todos los imports
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="autogen.import_utils")
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="chromadb.api.collection_configuration"
)

import asyncio
import logging
import os
import sys
import threading
from collections.abc import Sequence

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, TextMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Ensure we use local src files over installed packages
sys.path.insert(0, os.getcwd())

# Import from new structure - import directly from prompts to avoid circular import
from src.config.prompts import (
    AGENT_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    CODER_AGENT_DESCRIPTION,
    PLANNING_AGENT_DESCRIPTION,
    PLANNING_AGENT_SYSTEM_MESSAGE,
)
from src.interfaces import CLIInterface

# Managers moved to __init__
from src.utils import HistoryViewer, LoggingModelClientWrapper, get_conversation_tracker, get_logger


class AgentOrchestrator:
    """Main CLI application for the code agent"""

    def __init__(
        self,
        *,
        debug: bool = False,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        ssl_verify: bool = None,
        headless: bool = False,
        agent_id: str = None,  # NEW: Unique identifier for this orchestrator instance
    ):
        """
        Initialize all agent components
        """

        log_level = logging.DEBUG if debug else logging.INFO
        self.logger = get_logger(log_file=None, level=log_level)  # Use default path
        self.conversation_tracker = get_conversation_tracker()

        # Unique agent identifier (for distinguishing main agent from subagents in logs)
        self.agent_id = agent_id if agent_id else "MAIN"
        self.is_subagent = agent_id is not None  # True if this is a subagent

        # Mode system: "agent" (with tools) or "chat" (without modification tools)
        self.current_mode = "agent"  # Default mode
        # Headless mode: disable user prompts (for subagents and background tasks)
        self.headless = headless

        # Log orchestrator initialization with ID
        self.logger.debug(
            f"[{self.agent_id}] Orchestrator initialized (headless={headless}, subagent={self.is_subagent})"
        )

        # Set headless context for current execution context
        from src.utils.headless_context import set_headless

        set_headless(headless)
        # Load configuration (API key, URL, model)
        from src.config import get_settings

        self.settings = get_settings(
            api_key=api_key, base_url=base_url, model=model, ssl_verify=ssl_verify
        )

        # Validate configuration (without interactivity in headless mode)
        is_valid, error_msg = self.settings.validate(interactive=not headless)
        if not is_valid:
            self.logger.error(f"[ERROR] Invalid configuration: {error_msg}")
            print(error_msg)
            raise ValueError("Invalid configuration")

        # DEEPSEEK REASONER SUPPORT
        # Use DeepSeekReasoningClient for models with thinking mode

        # Create custom HTTP client with SSL configuration
        import httpx

        http_client = httpx.AsyncClient(verify=self.settings.ssl_verify)

        # Complete JSON logging system (ALWAYS active, independent of Langfuse)
        # IMPORTANT: Initialize JSONLogger BEFORE creating the model_client wrapper
        from src.utils.json_logger import JSONLogger

        self.json_logger = JSONLogger()

        # =====================================================================
        # DYNAMIC MODEL CLIENTS (Base vs Strong)
        # =====================================================================

        # 1. Base Client (lighter/faster) - Usually deepseek-chat or gpt-4o-mini
        # For base model we typically use standard client (no reasoning usually needed)
        self.client_base = OpenAIChatCompletionClient(
            model=self.settings.base_model,
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            model_info=self.settings.get_model_capabilities(),
            custom_http_client=http_client,
        )

        # 2. Strong Client (Reasoning/Powerful) - Usually deepseek-reasoner or gpt-4o
        from src.utils.deepseek_reasoning_client import DeepSeekReasoningClient

        # Check if strong model needs reasoning client
        is_deepseek_reasoner = (
            "deepseek-reasoner" in self.settings.strong_model.lower()
            and "deepseek" in self.settings.base_url.lower()
        )

        if is_deepseek_reasoner:
            self.client_strong = DeepSeekReasoningClient(
                model=self.settings.strong_model,
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                model_info=self.settings.get_model_capabilities(),
                custom_http_client=http_client,
                enable_thinking=None,  # Auto detect
            )

        else:
            self.client_strong = OpenAIChatCompletionClient(
                model=self.settings.strong_model,
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                model_info=self.settings.get_model_capabilities(),
                custom_http_client=http_client,
            )

        # Wrappers for Logging
        # Note: We will wrap them again with specific agent names later,
        # but here we set up the default 'model_client' for compatibility with rest of init

        # Default model client (starts as Strong for compatibility)
        self.model_client = LoggingModelClientWrapper(
            wrapped_client=self.client_strong,
            json_logger=self.json_logger,
            agent_name="SystemRouter",
        )

        # ROUTER CLIENT: Always use Base Model for routing/planning
        self.router_client = OpenAIChatCompletionClient(
            model=self.settings.base_model,  # Use base model for router
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            model_info=self.settings.get_model_capabilities(),
            custom_http_client=http_client,
        )

        # Agent Skills system
        from src.skills import SkillManager

        self.skill_manager = SkillManager(logger=self.logger.logger)
        skill_count = self.skill_manager.discover_skills()
        if skill_count > 0:
            self.logger.info(f"✓ Loaded {skill_count} agent skills")
        else:
            self.logger.debug("No agent skills found (check .daveagent/skills/ directories)")

        # Context Manager (DAVEAGENT.md)
        from src.managers import ContextManager

        self.context_manager = ContextManager(logger=self.logger)
        context_files = self.context_manager.discover_context_files()
        if context_files:
            self.logger.info(f"✓ Found {len(context_files)} DAVEAGENT.md context file(s)")
        else:
            self.logger.debug("No DAVEAGENT.md context files found")

        # Error Reporter (sends errors to SigNoz instead of creating GitHub issues)
        from src.managers import ErrorReporter

        self.error_reporter = ErrorReporter(logger=self.logger)

        # Observability system with Langfuse (simple method with OpenLit)
        # Observability system with Langfuse (simple method with OpenLit)
        # MOVED TO BACKGROUND COMPONENT (THREAD) to avoid blocking startup (40s delay)
        self.langfuse_enabled = False  # Will be set to True by background thread eventually

        def init_telemetry_background():
            try:
                # Setup Langfuse environment from obfuscated credentials
                from src.config import is_telemetry_enabled, setup_langfuse_environment

                if is_telemetry_enabled():
                    # Check first if we should even proceed, to avoid heavy imports
                    setup_langfuse_environment()

                    # Initialize Langfuse with OpenLit (automatic AutoGen tracking)
                    from src.observability import init_langfuse_tracing

                    if init_langfuse_tracing(enabled=True, debug=debug):
                        self.langfuse_enabled = True
                        # Use print because logger might not be thread-safe or visible yet
                        # but we want to confirm it loaded
                        if debug:
                            print("[Background] ✓ Telemetry enabled - Langfuse + OpenLit active")
                    else:
                        if debug:
                            print(
                                "[Background] ✗ Langfuse not available - continuing without tracking"
                            )
            except Exception as e:
                if debug:
                    print(f"[Background] ✗ Error initializing Langfuse: {e}")

        # Start telemetry in background
        threading.Thread(target=init_telemetry_background, daemon=True).start()

        # Import all tools from the new structure
        from src.tools import (
            # Analysis
            analyze_python_file,
            csv_info,
            csv_to_json,
            delete_file,
            edit_file,
            file_search,
            filter_csv,
            find_function_definition,
            format_json,
            git_add,
            git_branch,
            git_commit,
            git_diff,
            git_log,
            git_pull,
            git_push,
            # Git
            git_status,
            glob_search,
            grep_search,
            json_get_value,
            json_set_value,
            json_to_text,
            list_all_functions,
            list_dir,
            merge_csv_files,
            merge_json_files,
            # CSV
            read_csv,
            # Filesystem
            read_file,
            # JSON
            read_json,
            run_terminal_cmd,
            sort_csv,
            validate_json,
            web_search,
            wiki_content,
            wiki_page_info,
            wiki_random,
            # Web
            wiki_search,
            wiki_set_language,
            wiki_summary,
            write_csv,
            write_file,
            write_json,
        )

        # Store all tools to filter them according to mode
        self.all_tools = {
            # READ-ONLY tools (available in both modes)
            "read_only": [
                read_file,
                list_dir,
                file_search,
                glob_search,
                git_status,
                git_log,
                git_branch,
                git_diff,
                read_json,
                validate_json,
                json_get_value,
                json_to_text,
                read_csv,
                csv_info,
                filter_csv,
                wiki_search,
                wiki_summary,
                wiki_content,
                wiki_page_info,
                wiki_random,
                wiki_set_language,
                web_search,
                analyze_python_file,
                find_function_definition,
                list_all_functions,
                grep_search,
            ],
            # MODIFICATION tools (only in agent mode)
            "modification": [
                write_file,
                edit_file,
                delete_file,
                git_add,
                git_commit,
                git_push,
                git_pull,
                write_json,
                merge_json_files,
                format_json,
                json_set_value,
                write_csv,
                merge_csv_files,
                csv_to_json,
                sort_csv,
                run_terminal_cmd,
            ],
        }

        # =====================================================================
        # MESSAGEBUS SYSTEM INITIALIZATION (FASE 3: Auto-Injection)
        # =====================================================================
        # Initialize MessageBus for auto-injection of system messages
        # Inspired by Nanobot's architecture for automatic result injection
        # =====================================================================
        from src.bus import MessageBus

        self.message_bus = MessageBus()
        self.logger.info("✓ MessageBus initialized for auto-injection")

        # System message detector (background task for auto-injection)
        self._detector_running = False
        self._detector_task = None

        # SUBAGENT SYSTEM INITIALIZATION
        # =====================================================================
        # Initialize parallel subagent execution system
        # This allows the agent to spawn background tasks that run concurrently
        # =====================================================================
        import sys

        from src.subagents import SubagentEventBus, SubAgentManager
        from src.tools import check_subagent_results, spawn_subagent

        self.subagent_event_bus = SubagentEventBus()
        self.subagent_manager = SubAgentManager(
            event_bus=self.subagent_event_bus,
            orchestrator_factory=self._create_subagent_orchestrator,
            base_tools=self.all_tools["read_only"] + self.all_tools["modification"],
            message_bus=self.message_bus,  # NEW: Pass MessageBus for auto-injection
        )

        # Initialize spawn tool with manager
        # Access the module from sys.modules to call set_subagent_manager
        spawn_module = sys.modules["src.tools.spawn_subagent"]
        spawn_module.set_subagent_manager(self.subagent_manager, task_id="main")

        # Add spawn tool to available tools
        self.all_tools["modification"].append(spawn_subagent)

        # Queue for pending subagent announcements (Nanobot-style)
        self._subagent_announcements = []

        # Initialize check_subagent_results tool with orchestrator reference
        check_results_module = sys.modules["src.tools.check_subagent_results"]
        check_results_module.set_orchestrator(self)

        # Add check results tool to read-only tools (doesn't modify state)
        self.all_tools["read_only"].append(check_subagent_results)

        # Initialize terminal tool with orchestrator reference (for real-time output)
        terminal_module = sys.modules["src.tools.terminal"]
        terminal_module.set_orchestrator(self)

        # Subscribe to subagent events
        self.subagent_event_bus.subscribe("spawned", self._on_subagent_spawned)
        self.subagent_event_bus.subscribe("completed", self._on_subagent_completed)
        self.subagent_event_bus.subscribe("failed", self._on_subagent_failed)

        # Cron system initialization
        from pathlib import Path

        from src.cron import CronService

        cron_storage = Path(os.getcwd()) / ".daveagent" / "cron_jobs.json"
        self.cron_service = CronService(
            storage_path=cron_storage, on_job=self._on_cron_job_triggered
        )
        self.logger.info("✓ Cron service initialized")

        # System components
        if headless:
            # Headless mode: without interactive CLI (for evaluations)
            self.cli = type(
                "DummyCLI",
                (),
                {
                    "print_success": lambda *args, **kwargs: None,
                    "print_error": lambda *args, **kwargs: None,
                    "print_info": lambda *args, **kwargs: None,
                    "print_thinking": lambda *args, **kwargs: None,
                    "print_agent_message": lambda *args, **kwargs: None,
                    "start_thinking": lambda *args, **kwargs: None,
                    "stop_thinking": lambda *args, **kwargs: None,
                    "mentioned_files": [],
                    "get_mentioned_files_content": lambda: "",
                    "print_mentioned_files": lambda: None,
                    "console": None,
                },
            )()
            self.history_viewer = None
        else:
            # Normal interactive mode
            self.cli = CLIInterface()
            self.history_viewer = HistoryViewer(console=self.cli.console)

        self.running = True

        # Initialize agents and main_team for the current mode
        self._initialize_agents_for_mode()

    def _initialize_agents_for_mode(self):
        """
        Initialize all system agents according to current mode

        AGENT mode: Coder with all tools + AGENT_SYSTEM_PROMPT
        CHAT  mode: Coder with read-only + CHAT_SYSTEM_PROMPT (more conversational)

        NOTE: Agents DO NOT use the parameter 'memory' de AutoGen para evitar
        errors with "multiple system messages" in models like DeepSeek.
        Instead, they use RAG tools (query_*_memory, save_*).
        """

        if self.current_mode == "agent":
            # AGENT mode: all tools + technical prompt
            coder_tools = self.all_tools["read_only"] + self.all_tools["modification"]
            system_prompt = AGENT_SYSTEM_PROMPT
        else:
            # CHAT mode: read-only + conversational prompt
            coder_tools = self.all_tools["read_only"]
            system_prompt = CHAT_SYSTEM_PROMPT

        # =====================================================================
        # SKILL METADATA IS NOW INJECTED DYNAMICALLY VIA RAG
        # =====================================================================
        # See process_user_request() where finding_relevant_skills is called
        # =====================================================================

        # =====================================================================
        # INJECT PROJECT CONTEXT (DAVEAGENT.md)
        # =====================================================================
        # Load specific instructions, commands, and guidelines from DAVEAGENT.md
        # =====================================================================
        project_context = self.context_manager.get_combined_context()
        if project_context:
            system_prompt = system_prompt + project_context
            self.logger.info("✓ Injected project context from DAVEAGENT.md")

        # =====================================================================
        # IMPORTANT: DO NOT use parameter 'memory' - CAUSES ERROR WITH DEEPSEEK
        # =====================================================================
        # DeepSeek and other LLMs do not support multiple system messages.
        # The parameter 'memory' in AutoGen injects additional system messages.
        #
        # SOLUTION: Use RAG tools instead (query_*_memory, save_*)
        # RAG tools are available in coder_tools and do not cause
        # conflicts with system messages.
        # =====================================================================

        # Create separate wrappers for each agent (for logging with correct names)

        # Create separate wrappers for each agent (for logging with correct names)
        # 1. Coder (Defaulting to Strong client, but will be switched dynamically)
        coder_client = LoggingModelClientWrapper(
            wrapped_client=self.client_strong,
            json_logger=self.json_logger,
            agent_name="Coder",
        )

        # 2. Planner (Always Base client)
        planner_client = LoggingModelClientWrapper(
            wrapped_client=self.client_base,
            json_logger=self.json_logger,
            agent_name="Planner",
        )

        coder_context = BufferedChatCompletionContext(buffer_size=100)
        planner_context = BufferedChatCompletionContext(buffer_size=100)

        # Create code agent with RAG tools (without memory parameter)
        self.coder_agent = AssistantAgent(
            name="Coder",
            description=CODER_AGENT_DESCRIPTION,
            system_message=system_prompt,
            model_client=coder_client,
            tools=coder_tools,  # Includes memory RAG tools
            max_tool_iterations=300,  # High limit for long-running tasks
            reflect_on_tool_use=True,  # Show agent reasoning before tool calls
            model_context=coder_context,  # Limit context to prevent token overflow
        )

        # PlanningAgent (without tools, without memory)
        self.planning_agent = AssistantAgent(
            name="Planner",
            description=PLANNING_AGENT_DESCRIPTION,
            system_message=PLANNING_AGENT_SYSTEM_MESSAGE,
            model_client=planner_client,
            tools=[],  # Planner has no tools, only plans
            model_context=planner_context,  # Limit context to prevent token overflow
        )

        # =====================================================================
        # ROUTER TEAM: Single SelectorGroupChat that routes automatically
        # =====================================================================
        # This team automatically decides which agent to use according to context:
        # - Planner: For complex multi-step tasks
        # - Coder: For code modifications and analysis
        #
        # Advantages:
        # - Does not need manual complexity detection
        # - Single team that persists (not recreated on each request)
        # - The LLM router decides intelligently
        # - Eliminates "multiple system messages" problem
        # =====================================================================

        termination_condition = TextMentionTermination("TERMINATE") | MaxMessageTermination(
            1000
        )  # High limit for long-running conversations

        self.logger.debug("[SELECTOR] Creating SelectorGroupChat...")
        self.logger.debug("[SELECTOR] Participants: Planner, Coder")

        def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
            # If no messages, start with Coder
            if not messages:
                self.logger.debug(
                    f"🔄 [{self.agent_id}] [Selector] No messages yet -> Starting with Coder"
                )
                return "Coder"

            last_message = messages[-1]
            content_preview = ""
            if hasattr(last_message, "content"):
                c = last_message.content
                content_preview = str(c)[:120].replace("\n", " ") if c else "(empty)"

            # Enhanced logging with agent_id prefix
            self.logger.debug(
                f"🔄 [{self.agent_id}] [Selector] msg[{len(messages) - 1}] from={last_message.source} "
                f"type={type(last_message).__name__}: {content_preview}"
            )

            # CRITICAL: If Planner just spoke, it's ALWAYS Coder's turn (never terminate after Planner)
            if last_message.source == "Planner":
                if isinstance(last_message, TextMessage):
                    if "TERMINATE" in last_message.content:
                        self.logger.debug(
                            f"🔄 [{self.agent_id}] [Selector] Planner said TERMINATE -> Ending conversation"
                        )
                        return None  # Let termination condition handle it
                self.logger.debug(
                    f"🔄 [{self.agent_id}] [Selector] Planner just spoke -> Selecting Coder (MANDATORY)"
                )
                return "Coder"

            # If Coder just spoke
            if last_message.source == "Coder":
                # Check for explicit signals in TextMessage
                if isinstance(last_message, TextMessage):
                    if "TERMINATE" in last_message.content:
                        self.logger.debug(
                            f"🔄 [{self.agent_id}] [Selector] Coder said TERMINATE -> Ending conversation"
                        )
                        return None  # Let termination condition handle it
                    content = last_message.content
                    if any(token in content for token in ("DELEGATE_TO_PLANNER", "SUBTASK_DONE")):
                        reason = (
                            "delegating to Planner"
                            if "DELEGATE_TO_PLANNER" in content
                            else "subtask done -> Back to Planner"
                        )
                        self.logger.debug(f"🔄 [{self.agent_id}] [Selector] Coder {reason}")
                        return "Planner"

                # If Coder just sent a tool call (AssistantMessage with tool calls)
                # We usually want Coder to receive the result.
                # But here we assume the runtime executes the tool and appends the result.
                # We want to ensure Coder gets the next turn to read the result.
                self.logger.debug(
                    f"🔄 [{self.agent_id}] [Selector] Coder waiting for tool result -> Keep Coder"
                )
                return "Coder"

            # If the last message was a tool execution result
            # (FunctionExecutionResultMessage usually has source='user' or the tool name, but definitely not 'Coder'/'Planner')
            # We must verify the type to be sure.
            if type(last_message).__name__ == "FunctionExecutionResultMessage":
                # Tool finished, give control back to Coder to handle the output
                self.logger.debug(
                    f"🔄 [{self.agent_id}] [Selector] Tool result received -> Back to Coder"
                )
                return "Coder"

            # If the last message is from the User
            if last_message.source == "user":
                # Default to Planner for normal requests
                self.logger.debug(
                    f"[{self.agent_id}] [Selector] User message -> Starting with Planner"
                )
                return "Planner"

            # FALLBACK: Never return None unless we explicitly want to terminate
            # If we don't recognize the source, default to Coder to continue
            self.logger.warning(
                f"⚠️ [{self.agent_id}] [Selector] Unknown message source: {last_message.source} -> Defaulting to Coder"
            )
            return "Coder"

        self.main_team = SelectorGroupChat(
            participants=[self.planning_agent, self.coder_agent],
            model_client=self.router_client,
            termination_condition=termination_condition,
            allow_repeated_speaker=True,  # Allows the same agent to speak multiple times
            selector_func=selector_func,
        )

        self.logger.debug(
            f"[SELECTOR] Router team created with {len(self.main_team._participants)} agents"
        )

    async def _update_agent_tools_for_mode(self):
        """
        Completely reinitialize the agent system according to current mode

        This creates new instances of all agents with the correct
        configuration for the mode (tools + system prompt).
        """

        # STEP 1: Clean current StateManager session
        if self.state_manager.session_id:
            self.logger.debug("🧹 Cleaning StateManager session...")
            self.state_manager.clear_current_session()

        # STEP 2: Reinitialize agents
        # Agents will use RAG tools instead of memory parameter
        self._initialize_agents_for_mode()

    # =========================================================================
    # SUBAGENT SYSTEM METHODS
    # =========================================================================

    def _create_subagent_orchestrator(
        self,
        tools: list,
        max_iterations: int,
        mode: str = "subagent",
        task: str = "",  # Task description for subagent prompt
        subagent_id: str = None,  # NEW: Unique identifier for logging
    ):
        """Factory method to create isolated AgentOrchestrator for subagents.

        This creates a new instance of AgentOrchestrator with:
        - Isolated tool set (no spawn_subagent to prevent recursion)
        - Limited max iterations (15 vs 25 for main agent)
        - Simplified execution mode (no full UI)
        - Custom system prompt specific to subagents
        - Unique ID for logging/debugging

        Args:
            tools: Filtered list of tools for the subagent
            max_iterations: Maximum iterations allowed
            mode: Execution mode (should be "subagent")
            task: Task description for the subagent (used in system prompt)
            subagent_id: Unique identifier for this subagent (auto-generated if None)

        Returns:
            New AgentOrchestrator instance configured for subagent use
        """
        # Generate subagent ID if not provided
        if not subagent_id:
            import uuid

            subagent_id = f"SUB-{str(uuid.uuid4())[:8]}"

        # Log subagent creation (DEBUG only - not shown in terminal)
        self.logger.debug(
            f"[{self.agent_id}] Creating subagent orchestrator with ID: {subagent_id}"
        )
        self.logger.debug(f"[{self.agent_id}] Subagent task: {task[:100]}...")

        # Create new instance with same config but isolated state
        subagent_orch = AgentOrchestrator(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
            model=self.settings.model,
            ssl_verify=self.settings.ssl_verify,
            headless=True,  # Subagents run in headless mode (no CLI)
            agent_id=subagent_id,  # Pass unique ID for logging
        )

        # Mark as subagent mode
        subagent_orch._is_subagent = True
        subagent_orch._subagent_max_iterations = max_iterations

        # Override coder agent tools with filtered set
        subagent_orch.coder_agent._tools = tools
        subagent_orch.coder_agent.max_tool_iterations = max_iterations

        # Log tool configuration (DEBUG only)
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]
        self.logger.debug(f"[{subagent_id}] Configured with tools: {', '.join(tool_names)}")
        self.logger.debug(f"[{subagent_id}] Max tool iterations: {max_iterations}")

        # IMPORTANT: Override system prompt with subagent-specific prompt
        if task:
            from pathlib import Path

            from src.config.prompts import SUBAGENT_SYSTEM_PROMPT

            workspace = Path.cwd()
            subagent_prompt = SUBAGENT_SYSTEM_PROMPT(task=task, workspace_path=str(workspace))
            # Update the system_message attribute (singular, not plural)
            subagent_orch.coder_agent._system_message = subagent_prompt
            self.logger.debug(f"[{subagent_id}] Custom system prompt applied")

        self.logger.debug(f"[{subagent_id}] Subagent orchestrator creation complete")
        return subagent_orch

    async def run_task(self, task: str) -> str:
        """Run a task using the agent team.

        This method is used both by the main task and by subagents.
        For subagents, it uses simplified execution (no full UI).

        Args:
            task: Task description to execute

        Returns:
            Result string from the agent execution
        """
        if hasattr(self, "_is_subagent") and self._is_subagent:
            # Simplified execution for subagents
            return await self._run_task_simple(task)
        else:
            # This shouldn't be called for main task - use process_user_request instead
            self.logger.warning(
                "run_task called on main orchestrator - use process_user_request instead"
            )
            return await self._run_task_simple(task)

    async def _run_task_simple(self, task: str) -> str:
        """Simplified task execution for subagents (no full UI).

        Args:
            task: Task to execute

        Returns:
            Collected result from agent execution
        """
        # Run through main_team
        stream = self.main_team.run_stream(task=[TextMessage(content=task, source="user")])

        # Collect result
        result_parts = []
        async for msg in stream:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                # Only collect TextMessage content from agents
                if hasattr(msg, "source") and msg.source in ["Coder", "Planner"]:
                    result_parts.append(msg.content)

        return "\n".join(result_parts) if result_parts else "Task completed"

    async def _on_subagent_spawned(self, event) -> None:
        """Handle subagent spawn event.

        Shows enhanced notification when a subagent is spawned.

        Args:
            event: SubagentEvent with spawn data
        """
        label = event.content.get("label", "unknown")
        task = event.content.get("task", "")

        # Show enhanced spawn notification
        self.cli.print_subagent_spawned(event.subagent_id, label, task)
        self.logger.info(f"Subagent {event.subagent_id} ({label}) spawned for task: {task[:100]}")

    async def _on_subagent_completed(self, event) -> None:
        """Handle subagent completion event.

        Nanobot-style: Queue the result for announcement to the main agent.
        The result will be summarized naturally in the next agent response.

        Args:
            event: SubagentEvent with completion data
        """
        label = event.content.get("label", "unknown")
        result = event.content.get("result", "")
        task = event.content.get("task", "")
        result_preview = result[:200] + "..." if len(result) > 200 else result

        # Show completion notification in terminal IMMEDIATELY
        self.cli.print_subagent_completed(event.subagent_id, label, result_preview)

        # Log completion
        self.logger.info(
            f"✓ Subagent '{label}' ({event.subagent_id[:8]}) completed: {result_preview}"
        )
        self.logger.info(f"Subagent {event.subagent_id} ({label}) completed successfully")

        # NANOBOT-STYLE: Create announcement message
        announce_content = f"""[Background Task Completed: '{label}']

Task: {task if task else "Unspecified task"}

Result:
{result}

---
Please summarize this result naturally for the user in 1-2 sentences.
Focus on the key findings or actions taken.
Do not mention technical terms like "subagent" or IDs."""

        # Queue announcement for display
        if hasattr(self, "_subagent_announcements"):
            self._subagent_announcements.append(
                {
                    "label": label,
                    "task": task,
                    "result": result,
                    "preview": result_preview,
                    "announcement": announce_content,
                }
            )
            self.logger.debug(f"Queued subagent announcement for '{label}'")

    async def _on_subagent_failed(self, event) -> None:
        """Handle subagent failure event.

        Nanobot-style: Queue the failure for announcement to the main agent.

        Args:
            event: SubagentEvent with failure data
        """
        label = event.content.get("label", "unknown")
        task = event.content.get("task", "")
        error = event.content.get("error", "Unknown error")

        # Show enhanced failure notification
        self.cli.print_subagent_failed(event.subagent_id, label, error)
        self.logger.error(f"Subagent {event.subagent_id} ({label}) failed: {error}")

        # NANOBOT-STYLE: Create failure announcement
        announce_content = f"""[Background Task Failed: '{label}']

Task: {task if task else "Unspecified task"}

Error:
{error}

---
Please inform the user about this failure in a clear way.
Suggest possible next steps or alternatives if appropriate."""

        # Queue announcement
        if hasattr(self, "_subagent_announcements"):
            self._subagent_announcements.append(
                {
                    "label": label,
                    "task": task,
                    "error": error,
                    "announcement": announce_content,
                    "failed": True,
                }
            )
            self.logger.debug(f"Queued subagent failure announcement for '{label}'")

    async def _on_cron_job_triggered(self, job) -> None:
        """Handle cron job trigger by spawning a subagent.

        When a cron job fires, spawn a subagent to execute the task.
        The subagent will run in the background and report results via announcements.

        Args:
            job: CronJob instance that was triggered
        """
        self.cli.print_info(f"⏰ Cron job triggered: {job.name}")
        self.logger.info(f"Cron job {job.id} ({job.name}) triggered at scheduled time")

        # Spawn subagent to execute the cron task
        if hasattr(self, "subagent_manager"):
            try:
                label = f"cron:{job.name[:30]}"
                subagent_id = await self.subagent_manager.spawn(
                    task=job.task, label=label, parent_task_id="cron", max_iterations=15
                )
                self.logger.info(f"Spawned subagent {subagent_id} for cron job {job.id}")
                self.cli.print_success(f"✓ Spawned subagent {subagent_id} for cron task")
            except Exception as e:
                self.logger.error(f"Failed to spawn subagent for cron job {job.id}: {e}")
                self.cli.print_error(f"✗ Failed to execute cron job: {e}")
        else:
            self.logger.warning("Subagent manager not available for cron job execution")
            self.cli.print_warning("⚠️ Cannot execute cron job - subagent system not initialized")

    # =========================================================================
    # SYSTEM MESSAGE DETECTOR (FASE 3: Auto-Injection)
    # =========================================================================
    # Background task that monitors MessageBus and automatically injects
    # system messages (subagent results, cron results) into agent conversation
    # =========================================================================

    async def start_system_message_detector(self):
        """Start the background system message detector.

        This launches a background asyncio task that continuously monitors
        the MessageBus for system messages and automatically injects them
        into the agent conversation (Nanobot-style).
        """
        if self._detector_running:
            self.logger.warning("System message detector already running")
            return

        self._detector_running = True
        self._detector_task = asyncio.create_task(self._system_message_detector())

    async def stop_system_message_detector(self):
        """Stop the background system message detector.

        Gracefully stops the detector task and waits for it to complete.
        """
        if not self._detector_running:
            return

        self._detector_running = False

        if self._detector_task:
            try:
                # Wait for detector to finish with timeout
                await asyncio.wait_for(self._detector_task, timeout=2.0)
            except TimeoutError:
                self.logger.warning("System message detector did not stop gracefully, cancelling")
                self._detector_task.cancel()
                try:
                    await self._detector_task
                except asyncio.CancelledError:
                    pass

        self.logger.info("✓ System message detector stopped")

    async def _system_message_detector(self):
        """Background task that detects and processes system announcements.

        This runs continuously in the background, monitoring the MessageBus
        for pending system messages. When a message arrives, it automatically
        injects it into the agent conversation as if the user sent it.

        This implements Nanobot-style auto-injection, eliminating the need
        for the agent to manually call check_subagent_results.
        """
        self.logger.debug("System message detector loop started")

        while self._detector_running:
            try:
                # Check for pending system messages (non-blocking with timeout)
                sys_msg = await self.message_bus.consume_inbound(timeout=0.5)

                if sys_msg:
                    self.logger.info(
                        f"Detected system message: {sys_msg.message_type} from {sys_msg.sender_id}"
                    )

                    try:
                        # Process the system message
                        await self._process_system_message(sys_msg)
                    except Exception as e:
                        self.logger.error(
                            f"Error processing system message from {sys_msg.sender_id}: {e}",
                            exc_info=True,
                        )
                        # Don't stop the detector on processing errors

            except Exception as e:
                self.logger.error(f"Error in system message detector: {e}", exc_info=True)
                # Brief sleep to avoid tight loop on persistent errors
                await asyncio.sleep(1.0)

        self.logger.debug("System message detector loop stopped")

    async def _process_system_message(self, sys_msg):
        """Process a system message and inject into agent conversation.

        This method takes a SystemMessage from the MessageBus and injects
        it into the agent's conversation context as if it were a user message.
        The agent then processes it naturally and responds to the user.

        This is the core of Nanobot-style auto-injection.

        Args:
            sys_msg: SystemMessage to process
        """
        self.logger.debug(f"Processing system message: {sys_msg.message_type}")

        # Display visual notification to user
        if sys_msg.message_type == "subagent_result":
            status = sys_msg.metadata.get("status", "ok")
            label = sys_msg.metadata.get("label", "unknown")

            if status == "ok":
                self.cli.print_success(f"📥 Subagent '{label}' completed - processing results...")
            else:
                self.cli.print_warning(f"📥 Subagent '{label}' failed - processing error...")
        elif sys_msg.message_type == "cron_result":
            self.cli.print_info("📥 Cron job result received - processing...")
        else:
            self.cli.print_info(f"📥 System message received: {sys_msg.message_type}")

        # Log to conversation tracker for persistence (always, regardless of team)
        if hasattr(self, "conversation_tracker"):
            try:
                self.conversation_tracker.add_message(
                    role="system",
                    content=sys_msg.content,
                    metadata={
                        "type": "subagent_result",
                        "message_type": sys_msg.message_type,
                        "sender_id": sys_msg.sender_id,
                        "timestamp": sys_msg.timestamp.isoformat()
                        if hasattr(sys_msg.timestamp, "isoformat")
                        else str(sys_msg.timestamp),
                        **sys_msg.metadata,
                    },
                )
                self.logger.debug("System message logged to conversation tracker")
            except Exception as log_error:
                self.logger.warning(f"Failed to log system message to tracker: {log_error}")

        # Check if we have an active team to process the message
        if not hasattr(self, "main_team") or self.main_team is None:
            # Fallback: just display the content if no team is active
            self.logger.warning("No active team - displaying system message directly")
            self.cli.print_info(f"\n{sys_msg.content}\n")
            return

        # Process message through LLM for natural response
        try:
            # Start thinking indicator
            self.cli.start_thinking()

            # Track for logging
            agent_messages_shown = set()
            spinner_active = True

            # Run team stream with the system message content
            # Get async generator directly for true streaming (don't wrap in Task)
            stream_generator = self.main_team.run_stream(task=sys_msg.content)

            try:
                # CRITICAL FIX: Iterate directly over async generator for streaming
                async for msg in stream_generator:
                    # Only process messages that are NOT from the user
                    if hasattr(msg, "source") and msg.source != "user":
                        agent_name = msg.source
                        msg_type = type(msg).__name__

                        # Determine message content
                        if hasattr(msg, "content"):
                            content = msg.content
                        else:
                            content = str(msg)

                        # Create unique key to avoid duplicates
                        try:
                            if isinstance(content, list):
                                content_str = str(content)
                            else:
                                content_str = content
                            message_key = f"{agent_name}:{hash(content_str)}"
                        except TypeError:
                            message_key = f"{agent_name}:{hash(str(content))}"

                        if message_key not in agent_messages_shown:
                            # Handle different message types
                            if msg_type == "ThoughtEvent":
                                # Show agent thoughts
                                if spinner_active:
                                    self.cli.stop_thinking(clear=True)
                                    spinner_active = False
                                self.cli.print_thinking(f"💭 {agent_name}: {content_str}")

                            elif msg_type == "ToolCallRequestEvent":
                                # Show tool calls
                                if spinner_active:
                                    self.cli.stop_thinking(clear=True)
                                    spinner_active = False
                                self.cli.print_info(f"🔧 {agent_name} calling tool...", agent_name)

                            elif msg_type == "ToolCallExecutionEvent":
                                # Show tool results (brief)
                                pass  # Don't show to avoid clutter

                            elif msg_type == "TextMessage":
                                # This is the final agent response
                                if spinner_active:
                                    self.cli.stop_thinking(clear=True)
                                    spinner_active = False
                                self.cli.print_agent_message(content_str, agent_name)

                            agent_messages_shown.add(message_key)

            except asyncio.CancelledError:
                self.logger.info("System message processing cancelled")
            finally:
                # Ensure spinner is stopped
                if spinner_active:
                    self.cli.stop_thinking(clear=True)

            self.logger.info(f"✓ System message from {sys_msg.sender_id} processed successfully")

        except Exception as e:
            self.logger.error(f"Error running agent with system message: {e}", exc_info=True)
            # Fallback: just display the content
            self.cli.stop_thinking(clear=True)
            self.cli.print_warning("⚠️ Could not process through agent, displaying directly:")
            self.cli.print_info(f"\n{sys_msg.content}\n")
