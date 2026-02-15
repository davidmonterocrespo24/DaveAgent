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
    ):
        """
        Initialize all agent components
        """

        log_level = logging.DEBUG if debug else logging.INFO
        self.logger = get_logger(log_file=None, level=log_level)  # Use default path
        self.conversation_tracker = get_conversation_tracker()
        # Mode system: "agent" (with tools) or "chat" (without modification tools)
        self.current_mode = "agent"  # Default mode
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

        # State management system (AutoGen save_state/load_state)
        from src.managers import StateManager

        self.state_manager = StateManager(
            auto_save_enabled=True,
            auto_save_interval=300,  # Auto-save every 5 minutes
            state_dir=os.path.join(os.getcwd(), ".daveagent", "state"),
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
            max_tool_iterations=25,
            reflect_on_tool_use=False,
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

        termination_condition = TextMentionTermination("TASK_COMPLETED") | MaxMessageTermination(50)

        self.logger.debug("[SELECTOR] Creating SelectorGroupChat...")
        self.logger.debug("[SELECTOR] Participants: Planner, Coder")
        self.logger.debug("[SELECTOR] Termination: TASK_COMPLETED or MaxMessages(50)")

        def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
            # No messages yet or last message is from the user:
            # let the LLM router decide (Planner vs Coder) based on task complexity
            if not messages:
                return None

            last_message = messages[-1]

            # User just sent a message — let LLM router decide who goes first
            if last_message.source == "user":
                return None

            # Planner just spoke — hand off to Coder for execution
            if last_message.source == "Planner":
                return "Coder"

            # Coder just spoke — check for explicit routing signals
            if last_message.source == "Coder":
                if isinstance(last_message, TextMessage):
                    if "TERMINATE" in last_message.content:
                        return None  # Let termination condition handle it
                    if "DELEGATE_TO_PLANNER" in last_message.content:
                        return "Planner"
                    if "SUBTASK_DONE" in last_message.content:
                        return "Planner"
                return "Coder"

            # Tool result — give control back to Coder to handle the output
            if type(last_message).__name__ == "FunctionExecutionResultMessage":
                return "Coder"

            # Default: let LLM router decide
            return None

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


