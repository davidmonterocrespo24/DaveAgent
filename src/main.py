"""
Main file - Complete CLI interface for the code agent
NEW REORGANIZED STRUCTURE (FIXED WITH LOGGING)
"""
import asyncio
import logging
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

# Imports added for the new flow
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

# from src.agents import CodeSearcher (Moved to __init__)
# Import from new structure
from src.config import (
    CODER_AGENT_DESCRIPTION,
    COMPLEXITY_DETECTOR_PROMPT,
    PLANNING_AGENT_DESCRIPTION,
    PLANNING_AGENT_SYSTEM_MESSAGE,
)
from src.config.prompts import AGENT_SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT
from src.interfaces import CLIInterface
from src.interfaces.vscode_interface import VSCodeInterface

# Managers moved to __init__
from src.utils import HistoryViewer, LoggingModelClientWrapper, get_conversation_tracker, get_logger


class DaveAgentCLI:
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
        vscode_mode: bool = False,
    ):
        """
        Initialize all agent components
        """
        import time
        t_start = time.time()

        # Configure logging (now in .daveagent/logs/)
        log_level = logging.DEBUG if debug else logging.INFO
        self.logger = get_logger(log_file=None, level=log_level)  # Use default path

        t0 = time.time()
        # Configure conversation tracker (logs to .daveagent/conversations.json)
        self.conversation_tracker = get_conversation_tracker()

        # Mode system: "agent" (with tools) or "chat" (without modification tools)
        self.current_mode = "agent"  # Default mode

        t0 = time.time()
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
            model=self.settings.base_model, # Use base model for router
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            model_capabilities=self.settings.get_model_capabilities(),
            http_client=http_client,
        )
        print(f"[Startup] Model clients initialized in {time.time() - t0:.4f}s")

        t0 = time.time()
        # State management system (AutoGen save_state/load_state)
        from src.managers import StateManager
        self.state_manager = StateManager(
            auto_save_enabled=True, auto_save_interval=300  # Auto-save every 5 minutes
        )
        print(f"[Startup] StateManager initialized in {time.time() - t0:.4f}s")

        t0 = time.time()
        # RAG Manager (Advanced retrieval system)
        print("[Startup] Importing RAGManager...")
        t_rag_import = time.time()
        from src.managers.rag_manager import RAGManager
        print(f"[Startup] RAGManager imported in {time.time() - t_rag_import:.4f}s")

        # Used for ContextManager search and SkillManager indexing
        # Initialize RAG Manager first
        # Use current working directory for rag_data persistence
        work_dir = os.getcwd()
        self.rag_manager = RAGManager(settings=self.settings, persist_dir=f"{work_dir}/.daveagent/rag_data")
        print(f"[Startup] RAGManager initialized in {time.time() - t0:.4f}s")

        t0 = time.time()
        # Agent Skills system (Claude-compatible and RAG-enhanced)
        from src.skills import SkillManager
        self.skill_manager = SkillManager(rag_manager=self.rag_manager, logger=self.logger)
        skill_count = self.skill_manager.discover_skills()
        if skill_count > 0:
            self.logger.info(f"✓ Loaded {skill_count} agent skills")
        else:
            self.logger.debug("No agent skills found (check .daveagent/skills/ directories)")
        print(f"[Startup] SkillManager initialized in {time.time() - t0:.4f}s")

        t0 = time.time()
        # Context Manager (DAVEAGENT.md)
        from src.managers import ContextManager
        self.context_manager = ContextManager(logger=self.logger)
        context_files = self.context_manager.discover_context_files()
        if context_files:
            self.logger.info(f"✓ Found {len(context_files)} DAVEAGENT.md context file(s)")
        else:
            self.logger.debug("No DAVEAGENT.md context files found")
        print(f"[Startup] ContextManager initialized in {time.time() - t0:.4f}s")

        # Error Reporter (sends errors to SigNoz instead of creating GitHub issues)
        from src.managers import ErrorReporter
        self.error_reporter = ErrorReporter(logger=self.logger)

        # Observability system with Langfuse (simple method with OpenLit)
        self.langfuse_enabled = False
        try:
            # Setup Langfuse environment from obfuscated credentials
            from src.config import is_telemetry_enabled, setup_langfuse_environment

            if is_telemetry_enabled():
                setup_langfuse_environment()

                # Initialize Langfuse with OpenLit (automatic AutoGen tracking)
                from src.observability import init_langfuse_tracing
                self.langfuse_enabled = init_langfuse_tracing(enabled=True, debug=debug)

                if self.langfuse_enabled:
                    self.logger.info("✓ Telemetry enabled - Langfuse + OpenLit active")
                else:
                    self.logger.info("✗ Langfuse not available - continuing without tracking")
            else:
                self.logger.info("📊 Telemetry disabled by user preference")
        except Exception as e:
            self.logger.warning(f"✗ Error initializing Langfuse: {e}")
            self.langfuse_enabled = False


        t0 = time.time()
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
        self.logger.info(f"[Startup] Tools imported in {time.time() - t0:.4f}s")

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

        self.logger.info(f"✨ DaveAgent initialized in {time.time() - t_start:.2f}s")

        # System components
        if vscode_mode:
            # VS Code mode: JSON output
            self.cli = VSCodeInterface()
            self.history_viewer = None
            self.logger.info("🔧 Initialized VSCodeInterface")
        elif headless:
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
        CHAT mode: Coder with read-only + CHAT_SYSTEM_PROMPT (more conversational)

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

        # Create code agent with RAG tools (without memory parameter)
        self.coder_agent = AssistantAgent(
            name="Coder",
            description=CODER_AGENT_DESCRIPTION,
            system_message=system_prompt,
            model_client=coder_client,
            tools=coder_tools,  # Includes memory RAG tools
            max_tool_iterations=25,
            reflect_on_tool_use=False,
            # NO memory parameter - uses RAG tools instead
        )

        # PlanningAgent (without tools, without memory)
        self.planning_agent = AssistantAgent(
            name="Planner",
            description=PLANNING_AGENT_DESCRIPTION,
            system_message=PLANNING_AGENT_SYSTEM_MESSAGE,
            model_client=planner_client,
            tools=[],  # Planner has no tools, only plans
            # NO memory parameter
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

        self.main_team = SelectorGroupChat(
            participants=[self.planning_agent, self.coder_agent],
            model_client=self.router_client,
            termination_condition=termination_condition,
            allow_repeated_speaker=True,  # Allows the same agent to speak multiple times
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

    async def handle_command(self, command: str) -> bool:
        """Handles special user commands"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd in ["/exit", "/quit"]:
            return False

        elif cmd == "/help":
            self.cli.print_help()

        elif cmd == "/clear":
            # Clear screen only - AutoGen handles history
            self.cli.clear_screen()
            self.cli.print_success("Screen cleared")

        elif cmd == "/new":
            # Just clear screen - new session will be auto-created if needed
            self.cli.clear_screen()
            self.cli.print_success("New conversation started")

        elif cmd == "/new-session":
            # Create new session with metadata
            await self._new_session_command(parts)

        elif cmd == "/save-state" or cmd == "/save-session":
            # Save complete state using AutoGen save_state
            await self._save_state_command(parts)

        elif cmd == "/load-state" or cmd == "/load-session":
            # Load state using AutoGen load_state
            await self._load_state_command(parts)

        elif cmd == "/list-sessions" or cmd == "/sessions":
            # List saved sessions with Rich table
            await self._list_sessions_command()

        elif cmd == "/history":
            # Show current session history
            await self._show_history_command(parts)

        elif cmd == "/init":
            # Create DAVEAGENT.md template
            try:
                path = self.context_manager.create_template()
                self.cli.print_success(f"✓ Created configuration file: {path}")
                self.cli.print_info("Edit this file to add project-specific commands and guidelines.")
            except Exception as e:
                self.cli.print_error(f"Error creating DAVEAGENT.md: {e}")

        # REMOVED: /load command - Use /load-state instead (AutoGen official)

        elif cmd == "/debug":
            # Change logging level
            current_level = self.logger.logger.level
            if current_level == logging.DEBUG:
                self.logger.logger.setLevel(logging.INFO)
                self.cli.print_success("🔧 Debug mode DISABLED (level: INFO)")
                self.logger.info("Logging level changed to INFO")
            else:
                self.logger.logger.setLevel(logging.DEBUG)
                self.cli.print_success("🐛 Debug mode ENABLED (level: DEBUG)")
                self.logger.debug("Logging level changed to DEBUG")

        elif cmd == "/logs":
            # Show log file location
            log_files = list(self.logger.logger.handlers)
            file_handlers = [h for h in log_files if isinstance(h, logging.FileHandler)]
            if file_handlers:
                log_path = file_handlers[0].baseFilename
                self.cli.print_info(f"📄 Log file: {log_path}")
            else:
                self.cli.print_info("No log files configured")

        elif cmd == "/modo-agent":
            # Switch to agent mode (with all tools)
            if self.current_mode == "agent":
                self.cli.print_info("Already in AGENT mode")
            else:
                self.current_mode = "agent"
                self.cli.set_mode("agent")  # Update CLI display
                await self._update_agent_tools_for_mode()
                self.cli.print_success("🔧 AGENT mode enabled")
                self.cli.print_info("✓ The agent can modify files and execute commands")

        elif cmd == "/modo-chat":
            # Switch to chat mode (read-only tools)
            if self.current_mode == "chat":
                self.cli.print_info("Already in CHAT mode")
            else:
                self.current_mode = "chat"
                self.cli.set_mode("chat")  # Update CLI display
                await self._update_agent_tools_for_mode()
                self.cli.print_success("💬 CHAT mode enabled")
                self.cli.print_info("✗ The agent CANNOT modify files or execute commands")
                self.cli.print_info("ℹ️  Use /modo-agent to return to full mode")

        elif cmd == "/config" or cmd == "/configuracion":
            # Show current configuration
            self.cli.print_info("\n⚙️  Current Configuration\n")
            masked_key = (
                f"{self.settings.api_key[:8]}...{self.settings.api_key[-4:]}"
                if self.settings.api_key
                else "Not configured"
            )
            self.cli.print_info(f"  • API Key: {masked_key}")
            self.cli.print_info(f"  • Base URL: {self.settings.base_url}")
            self.cli.print_info(f"  • Model: {self.settings.model}")
            self.cli.print_info(f"  • SSL Verify: {self.settings.ssl_verify}")
            self.cli.print_info(f"  • Mode: {self.current_mode.upper()}")
            self.cli.print_info("\n💡 Available commands:")
            self.cli.print_info("  • /set-model <model> - Change the model")
            self.cli.print_info("  • /set-url <url> - Change the base URL")
            self.cli.print_info("  • /set-ssl <true|false> - Change SSL verification")
            self.cli.print_info("\n📄 Configuration file: .daveagent/.env")

        elif cmd == "/set-model":
            # Change the model
            if len(parts) < 2:
                self.cli.print_error("Usage: /set-model <model-name>")
                self.cli.print_info("\nExamples:")
                self.cli.print_info("  /set-model deepseek-chat")
                self.cli.print_info("  /set-model deepseek-reasoner")
                self.cli.print_info("  /set-model gpt-4")
            else:
                new_model = parts[1]
                old_model = self.settings.model
                self.settings.model = new_model
                # Update wrapped client's model (access through _wrapped)
                if hasattr(self.model_client, "_wrapped"):
                    self.model_client._wrapped._model = new_model
                self.cli.print_success(f"✓ Model changed: {old_model} → {new_model}")
                self.logger.info(f"Model changed from {old_model} to {new_model}")

        elif cmd == "/set-url":
            # Change the base URL
            if len(parts) < 2:
                self.cli.print_error("Usage: /set-url <base-url>")
                self.cli.print_info("\nExamples:")
                self.cli.print_info("  /set-url https://api.deepseek.com")
                self.cli.print_info("  /set-url https://api.openai.com/v1")
            else:
                new_url = parts[1]
                old_url = self.settings.base_url
                self.settings.base_url = new_url
                # Update wrapped client's base URL (access through _wrapped)
                if hasattr(self.model_client, "_wrapped"):
                    self.model_client._wrapped._base_url = new_url
                self.cli.print_success(f"✓ URL changed: {old_url} → {new_url}")
                self.logger.info(f"Base URL changed from {old_url} to {new_url}")

        elif cmd == "/set-ssl":
            # Change SSL verification
            if len(parts) < 2:
                self.cli.print_error("Usage: /set-ssl <true|false>")
                self.cli.print_info("\nExamples:")
                self.cli.print_info("  /set-ssl true   # Verify SSL certificates (default)")
                self.cli.print_info("  /set-ssl false  # Disable SSL verification")
                self.cli.print_warning("\n⚠️  Warning: Disabling SSL reduces security")
            else:
                ssl_value = parts[1].lower()
                if ssl_value in ("true", "1", "yes", "on"):
                    new_ssl = True
                elif ssl_value in ("false", "0", "no", "off"):
                    new_ssl = False
                else:
                    self.cli.print_error(f"Invalid value: {ssl_value}")
                    self.cli.print_info("Use: true or false")
                    return True

                old_ssl = self.settings.ssl_verify
                self.settings.ssl_verify = new_ssl

                # Recreate HTTP client with new SSL configuration
                import httpx

                http_client = httpx.AsyncClient(verify=new_ssl)

                # Update model client (access through _wrapped)
                if hasattr(self.model_client, "_wrapped"):
                    # It's LoggingModelClientWrapper, update wrapped client
                    self.model_client._wrapped._http_client = http_client

                self.cli.print_success(f"✓ SSL Verify changed: {old_ssl} → {new_ssl}")
                if not new_ssl:
                    self.cli.print_warning(
                        "⚠️  SSL verification disabled - Connections are not secure"
                    )
                self.logger.info(f"SSL verify changed from {old_ssl} to {new_ssl}")


        elif cmd == "/skills":
            # List available agent skills
            await self._list_skills_command()

        elif cmd == "/skill-info":
            # Show skill details
            if len(parts) < 2:
                self.cli.print_error("Usage: /skill-info <skill-name>")
                self.cli.print_info("Use /skills to see available skills")
            else:
                await self._show_skill_info_command(parts[1])

        elif cmd == "/telemetry-off":
            # Disable telemetry
            from src.config import is_telemetry_enabled, set_telemetry_enabled
            if not is_telemetry_enabled():
                self.cli.print_info("📊 Telemetry is already disabled")
            else:
                set_telemetry_enabled(False)
                self.cli.print_success("📊 Telemetry disabled")
                self.cli.print_info("ℹ️  Changes will take effect on next restart")

        elif cmd == "/telemetry-on":
            # Enable telemetry
            from src.config import is_telemetry_enabled, set_telemetry_enabled
            if is_telemetry_enabled():
                self.cli.print_info("📊 Telemetry is already enabled")
            else:
                set_telemetry_enabled(True)
                self.cli.print_success("📊 Telemetry enabled")
                self.cli.print_info("ℹ️  Changes will take effect on next restart")

        elif cmd == "/telemetry":
            # Show telemetry status
            from src.config import is_telemetry_enabled
            status = "enabled" if is_telemetry_enabled() else "disabled"
            runtime = "active" if self.langfuse_enabled else "inactive"
            self.cli.print_info(f"📊 Telemetry status: {status}")
            self.cli.print_info(f"📊 Runtime status: {runtime}")
            if not is_telemetry_enabled():
                self.cli.print_info("ℹ️  Use /telemetry-on to enable telemetry")
            else:
                self.cli.print_info("ℹ️  Use /telemetry-off to disable telemetry")

        else:
            self.cli.print_error(f"Unknown command: {cmd}")
            self.cli.print_info("Use /help to see available commands")

        return True

    # =========================================================================
    # SKILLS MANAGEMENT - Agent Skills (Claude-compatible)
    # =========================================================================

    async def _list_skills_command(self):
        """List all available agent skills"""
        try:
            skills = self.skill_manager.get_all_skills()

            if not skills:
                self.cli.print_info("\n🎯 No agent skills loaded")
                self.cli.print_info("\nTo add skills, create directories with SKILL.md files in:")
                self.cli.print_info(f"  • Personal: {self.skill_manager.personal_skills_dir}")
                self.cli.print_info(f"  • Project: {self.skill_manager.project_skills_dir}")
                return

            self.cli.print_info(f"\n🎯 Available Agent Skills ({len(skills)} loaded)\n")

            # Group by source
            personal_skills = [s for s in skills if s.source == "personal"]
            project_skills = [s for s in skills if s.source == "project"]
            plugin_skills = [s for s in skills if s.source == "plugin"]

            if personal_skills:
                self.cli.print_info("📁 Personal Skills:")
                for skill in personal_skills:
                    desc = skill.description[:60] + "..." if len(skill.description) > 60 else skill.description
                    self.cli.print_info(f"  • {skill.name}: {desc}")

            if project_skills:
                self.cli.print_info("\n📂 Project Skills:")
                for skill in project_skills:
                    desc = skill.description[:60] + "..." if len(skill.description) > 60 else skill.description
                    self.cli.print_info(f"  • {skill.name}: {desc}")

            if plugin_skills:
                self.cli.print_info("\n🔌 Plugin Skills:")
                for skill in plugin_skills:
                    desc = skill.description[:60] + "..." if len(skill.description) > 60 else skill.description
                    self.cli.print_info(f"  • {skill.name}: {desc}")

            self.cli.print_info("\n💡 Use /skill-info <name> for details")

        except Exception as e:
            self.logger.log_error_with_context(e, "_list_skills_command")
            self.cli.print_error(f"Error listing skills: {str(e)}")

    async def _show_skill_info_command(self, skill_name: str):
        """Show detailed information about a skill"""
        try:
            skill = self.skill_manager.get_skill(skill_name)

            if not skill:
                self.cli.print_error(f"Skill not found: {skill_name}")
                self.cli.print_info("Use /skills to see available skills")
                return

            self.cli.print_info(f"\n🎯 Skill: {skill.name}\n")
            self.cli.print_info(f"📝 Description: {skill.description}")
            self.cli.print_info(f"📁 Source: {skill.source}")
            self.cli.print_info(f"📂 Path: {skill.path}")

            if skill.allowed_tools:
                self.cli.print_info(f"🔧 Allowed Tools: {', '.join(skill.allowed_tools)}")

            if skill.license:
                self.cli.print_info(f"📜 License: {skill.license}")

            # Show available resources
            resources = []
            if skill.has_scripts:
                scripts = [s.name for s in skill.get_scripts()]
                resources.append(f"Scripts: {', '.join(scripts)}")
            if skill.has_references:
                refs = [r.name for r in skill.get_references()]
                resources.append(f"References: {', '.join(refs)}")
            if skill.has_assets:
                resources.append("Assets: available")

            if resources:
                self.cli.print_info("\n📦 Resources:")
                for res in resources:
                    self.cli.print_info(f"  • {res}")

            # Show first part of instructions
            if skill.instructions:
                preview = skill.instructions[:500]
                if len(skill.instructions) > 500:
                    preview += "..."
                self.cli.print_info(f"\n📋 Instructions Preview:\n{preview}")

        except Exception as e:
            self.logger.log_error_with_context(e, "_show_skill_info_command")
            self.cli.print_error(f"Error showing skill info: {str(e)}")

    # =========================================================================
    # STATE MANAGEMENT - State management with AutoGen save_state/load_state
    # =========================================================================

    async def _new_session_command(self, parts: list):
        """
        Command /new-session: Create a new session with metadata

        Usage:
            /new-session <title>
            /new-session "My web project" --tags backend,api --desc "REST API with FastAPI"
        """
        try:
            # Parse arguments
            import shlex

            if len(parts) < 2:
                self.cli.print_error(
                    "Usage: /new-session <title> [--tags tag1,tag2] [--desc description]"
                )
                self.cli.print_info(
                    'Example: /new-session "Web Project" --tags python,web --desc "API Development"'
                )
                return

            # Join and parse
            cmd_str = " ".join(parts[1:])

            # Extract title (first argument)
            args = shlex.split(cmd_str)
            if not args:
                self.cli.print_error("You must provide a title for the session")
                return

            title = args[0]
            tags = []
            description = ""

            # Parse optional flags
            i = 1
            while i < len(args):
                if args[i] == "--tags" and i + 1 < len(args):
                    tags = [t.strip() for t in args[i + 1].split(",")]
                    i += 2
                elif args[i] == "--desc" and i + 1 < len(args):
                    description = args[i + 1]
                    i += 2
                else:
                    i += 1

            # Generate session_id
            from datetime import datetime

            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Start new session with metadata
            self.state_manager.start_session(
                session_id=session_id, title=title, tags=tags, description=description
            )

            self.cli.print_success(f"✅ New session created: {title}")
            self.cli.print_info(f"  • Session ID: {session_id}")
            if tags:
                self.cli.print_info(f"  • Tags: {', '.join(tags)}")
            if description:
                self.cli.print_info(f"  • Description: {description}")

            self.logger.info(f"✅ New session created: {session_id} - {title}")

        except Exception as e:
            self.logger.log_error_with_context(e, "_new_session_command")
            self.cli.print_error(f"Error creating session: {str(e)}")

    async def _generate_session_title(self) -> str:
        """
        Generate a descriptive title for the session using LLM based on history

        Returns:
            Generated title (maximum 50 characters)
        """
        try:
            # Get messages from current history
            messages = self.state_manager.get_session_history()

            if not messages or len(messages) < 2:
                return "Untitled Session"

            # Take first messages to understand context
            context_messages = messages[:5]  # First 5 messages

            # Format context
            conversation_summary = ""
            for msg in context_messages:
                role = msg.get("source", "unknown")
                content = msg.get("content", "")
                # Limit length of each message
                content_preview = content[:200] if len(content) > 200 else content
                conversation_summary += f"{role}: {content_preview}\n"

            # Create prompt to generate title
            title_prompt = f"""Based on the following conversation, generate a short, descriptive title (maximum 50 characters).
The title should capture the main topic or task being discussed.

CONVERSATION:
{conversation_summary}

Generate ONLY the title text, nothing else. Make it concise and descriptive.
Examples: "Python API Development", "Bug Fix in Authentication", "Database Migration Setup"

TITLE:"""

            # Call the LLM
            from autogen_core.models import UserMessage

            result = await self.model_client.create(
                messages=[UserMessage(content=title_prompt, source="user")]
            )

            # Extract title
            title = result.content.strip()

            # Clean title (remove quotes, etc.)
            title = title.strip('"').strip("'").strip()

            # Limit length
            if len(title) > 50:
                title = title[:47] + "..."

            self.logger.info(f"📝 Title generated: {title}")
            return title

        except Exception as e:
            self.logger.warning(f"Error generating title: {e}")
            return "Untitled Session"

    async def _auto_save_agent_states(self):
        """
        Auto-save the state of all agents after each response.
        Runs silently in background.
        Generates an automatic title if the session doesn't have one.
        """
        try:
            # Start session if not started
            if not self.state_manager.session_id:
                from datetime import datetime

                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Generate title automatically using LLM
                title = await self._generate_session_title()

                self.state_manager.start_session(session_id=session_id, title=title)

            # Save state of each agent
            await self.state_manager.save_agent_state(
                "coder", self.coder_agent, metadata={"description": "Main coder agent with tools"}
            )


            await self.state_manager.save_agent_state(
                "planning",
                self.planning_agent,
                metadata={"description": "Planning and task management agent"},
            )

            # Save to disk
            await self.state_manager.save_to_disk()

            self.logger.debug("💾 Auto-save: State saved automatically")

        except Exception as e:
            # Don't fail if auto-save fails, just log
            self.logger.warning(f"⚠️ Auto-save failed: {str(e)}")

    async def _save_state_command(self, parts: list):
        """
        Command /save-state or /save-session: Save complete state of agents and teams

        Usage:
            /save-state                  # Save current session
            /save-state <title>          # Save with specific title (create new session)
            /save-session <title>        # Alias
        """
        try:
            self.cli.start_thinking(message="saving session")
            self.logger.info("💾 Saving agent states...")

            # Determine if it's a new session or update
            if len(parts) > 1 and not self.state_manager.session_id:
                # New session with manual title
                title = " ".join(parts[1:])
                from datetime import datetime

                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

                self.state_manager.start_session(session_id=session_id, title=title)
            elif not self.state_manager.session_id:
                # Auto-generate session with automatic title using LLM
                from datetime import datetime

                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Generate smart title
                title = await self._generate_session_title()

                self.state_manager.start_session(session_id=session_id, title=title)
                self.logger.info(f"📝 Title generated automatically: {title}")
            else:
                # Update existing session
                session_id = self.state_manager.session_id

            # Save state of each agent
            await self.state_manager.save_agent_state(
                "coder", self.coder_agent, metadata={"description": "Main coder agent with tools"}
            )



            await self.state_manager.save_agent_state(
                "planning",
                self.planning_agent,
                metadata={"description": "Planning and task management agent"},
            )

            # Save to disk
            state_path = await self.state_manager.save_to_disk(session_id)

            self.cli.stop_thinking()

            # Get metadata and messages for display
            metadata = self.state_manager.get_session_metadata()
            messages = self.state_manager.get_session_history()

            self.cli.print_success("✅ State saved successfully!")
            self.cli.print_info(f"  • Title: {metadata.get('title', 'Untitled')}")
            self.cli.print_info(f"  • Session ID: {session_id}")
            self.cli.print_info(f"  • Location: {state_path}")
            self.cli.print_info("  • Agents saved: 3")
            self.cli.print_info(f"  • Messages saved: {len(messages)}")

            self.logger.info(f"✅ State saved in session: {session_id}")

        except Exception as e:
            self.cli.stop_thinking()
            self.logger.log_error_with_context(e, "_save_state_command")
            self.cli.print_error(f"Error saving state: {str(e)}")

    async def _load_state_command(self, parts: list):
        """
        Command /load-state or /load-session: Load agent state from a session
        and display complete history

        Usage:
            /load-state                  # Load most recent session
            /load-state my_session       # Load specific session
            /load-session <session_id>   # Alias
        """
        try:
            self.cli.start_thinking(message="loading session")
            self.logger.info("📂 Loading agent states...")

            # Determine session_id
            if len(parts) > 1:
                session_id = parts[1]
            else:
                # Use most recent session
                sessions = self.state_manager.list_sessions()
                if not sessions:
                    self.cli.stop_thinking()
                    if self.history_viewer:
                        self.history_viewer.display_no_sessions()
                    return

                session_id = sessions[0]["session_id"]
                title = sessions[0].get("title", "Most recent session")
                if self.history_viewer:
                    self.history_viewer.display_loading_session(session_id, title)

            # Load from disk
            loaded = await self.state_manager.load_from_disk(session_id)

            if not loaded:
                self.cli.stop_thinking()
                self.cli.print_error(f"Session not found: {session_id}")
                return

            # Load state into each agent
            agents_loaded = 0

            if await self.state_manager.load_agent_state("coder", self.coder_agent):
                agents_loaded += 1



            if await self.state_manager.load_agent_state("planning", self.planning_agent):
                agents_loaded += 1

            self.cli.stop_thinking()

            # Get session metadata and history
            metadata = self.state_manager.get_session_metadata()
            messages = self.state_manager.get_session_history()

            # Display session info
            if self.history_viewer:
                self.history_viewer.display_session_loaded(
                    session_id=session_id,
                    total_messages=len(messages),
                    agents_restored=agents_loaded,
                )

                # Display session metadata
                self.history_viewer.display_session_metadata(metadata, session_id)

            # Display conversation history
            if messages:
                self.cli.print_info("📜 Displaying conversation history:\n")
                if self.history_viewer:
                    self.history_viewer.display_conversation_history(
                        messages=messages,
                        max_messages=20,
                        show_thoughts=False,  # Show last 20 messages
                    )

                if len(messages) > 20:
                    self.cli.print_info(f"💡 Showing last 20 of {len(messages)} messages")
                    self.cli.print_info("💡 Use /history --all to see all messages")
            else:
                self.cli.print_warning("⚠️ No messages in this session's history")

            self.cli.print_info("\n✅ The agent will continue from where the conversation left off")
            self.logger.info(f"✅ State loaded from session: {session_id}")

        except Exception as e:
            self.cli.stop_thinking()
            self.logger.log_error_with_context(e, "_load_state_command")
            self.cli.print_error(f"Error loading state: {str(e)}")

    async def _list_sessions_command(self):
        """
        Command /list-sessions or /sessions: List all saved sessions with Rich
        """
        try:
            sessions = self.state_manager.list_sessions()

            if not sessions:
                if self.history_viewer:
                    self.history_viewer.display_no_sessions()
                return

            # Display sessions using Rich table
            if self.history_viewer:
                self.history_viewer.display_sessions_list(sessions)

            self.cli.print_info("💡 Use /load-session <session_id> to load a session")
            self.cli.print_info("💡 Use /history to view current session history")

        except Exception as e:
            self.logger.log_error_with_context(e, "_list_sessions_command")
            self.cli.print_error(f"Error listing sessions: {str(e)}")

    async def _show_history_command(self, parts: list):
        """
        Command /history: Display current session history

        Usage:
            /history              # Show last 20 messages
            /history --all        # Show all messages
            /history --thoughts   # Include thoughts/reasoning
            /history <session_id> # Show specific session history
        """
        try:
            # Parse options
            show_all = "--all" in parts
            show_thoughts = "--thoughts" in parts

            # Check if session_id provided
            session_id = None
            for part in parts[1:]:
                if not part.startswith("--"):
                    session_id = part
                    break

            # Get session history
            if session_id:
                # Load specific session history
                messages = self.state_manager.get_session_history(session_id)
                metadata = self.state_manager.get_session_metadata(session_id)
            else:
                # Use current session
                if not self.state_manager.session_id:
                    self.cli.print_warning("⚠️ No active session")
                    self.cli.print_info("💡 Use /load-session <id> to load a session")
                    self.cli.print_info("💡 Or use /new-session <title> to create a new one")
                    return

                messages = self.state_manager.get_session_history()
                metadata = self.state_manager.get_session_metadata()
                session_id = self.state_manager.session_id

            if not messages:
                self.cli.print_warning("⚠️ No messages in this session's history")
                return

            # Display metadata
            if self.history_viewer:
                self.history_viewer.display_session_metadata(metadata, session_id)

                # Display history
                max_messages = None if show_all else 20
                self.history_viewer.display_conversation_history(
                    messages=messages, max_messages=max_messages, show_thoughts=show_thoughts
                )

            # Show info about truncation
            if not show_all and len(messages) > 20:
                self.cli.print_info(f"\n💡 Showing last 20 of {len(messages)} messages")
                self.cli.print_info("💡 Use /history --all to see all messages")

        except Exception as e:
            self.logger.log_error_with_context(e, "_show_history_command")
            self.cli.print_error(f"Error showing history: {str(e)}")

    # =========================================================================
    # COMPLEXITY DETECTION - Task complexity detection
    # =========================================================================

    async def _detect_task_complexity(self, user_input: str) -> str:
        """
        🔀 SIMPLE ROUTER: Detect complexity with direct model call.

        Does NOT use agents, only calls the model with an optimized prompt.

        FLOWS:
        - SIMPLE → SelectorGroupChat (CodeSearcher + Coder)
        - COMPLEX → Planner + TaskExecutor + Agents

        Returns:
            "simple" or "complex"
        """
        try:
            self.logger.debug("🔀 Router: analyzing complexity...")

            # Create prompt with user request
            prompt = COMPLEXITY_DETECTOR_PROMPT.format(user_input=user_input)

            # DIRECT call to model (without agents, faster)
            from autogen_core.models import UserMessage

            result = await self.model_client.create(
                messages=[UserMessage(content=prompt, source="user")]
            )

            # Extract and parse JSON response
            response = result.content.strip()
            self.logger.debug(f"🔀 Model response: {response[:200]}")

            # Parse JSON
            import json
            import re

            try:
                # Clean markdown if it exists (some models add ```json```)
                json_match = re.search(r'\{[^{}]*"complexity"[^{}]*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    response_data = json.loads(json_str)
                    complexity = response_data.get("complexity", "simple").lower()
                    reasoning = response_data.get("reasoning", "No reasoning provided")

                    self.logger.info(f"✅ Router decided: {complexity.upper()}")
                    self.logger.debug(f"   Reasoning: {reasoning}")
                else:
                    # Fallback: search for the word in the response
                    self.logger.warning("⚠️ Valid JSON not found, using fallback")
                    if "complex" in response.lower():
                        complexity = "complex"
                    else:
                        complexity = "simple"
                    self.logger.warning(f"   Fallback decided: {complexity}")

            except json.JSONDecodeError as e:
                # If JSON parsing fails, use simple fallback
                self.logger.warning(f"⚠️ Error parsing JSON: {e}, using fallback")
                if "complex" in response.lower():
                    complexity = "complex"
                else:
                    complexity = "simple"
                self.logger.warning(f"   Fallback decided: {complexity}")

            return complexity

        except Exception as e:
            # Safe fallback
            self.logger.error(f"❌ Error in router: {str(e)}")
            self.logger.warning("⚠️ Fallback: using SIMPLE flow")
            return "simple"


    # =========================================================================
    # COMPLEX TASK EXECUTION - SelectorGroupChat with selector_func
    # =========================================================================

    async def _execute_complex_task(self, user_input: str):
        """
        Execute complex tasks using SelectorGroupChat with dynamic re-planning.

        ARCHITECTURE:
        - PlanningAgent: Create plan, review progress, re-plan
        - CodeSearcher: Search and analyze existing code
        - Coder: Execute modifications, create files

        FLOW:
        1. Planner creates initial plan
        2. LLM Selector chooses CodeSearcher or Coder for each task
        3. selector_func forces Planner to review after each action
        4. Planner can re-plan if necessary
        5. When everything is complete, Planner marks TASK_COMPLETED
        """
        try:
            self.logger.info("🎯 Using COMPLEX flow: SelectorGroupChat + re-planning")
            self.cli.print_info("📋 Complex task detected. Starting planning...\n")

            # Custom selection function for dynamic re-planning
            def custom_selector_func(messages):
                """
                Control flow to allow re-planning:
                - After Planner → LLM Selector decides (Coder/CodeSearcher)
                - After Coder/CodeSearcher → Return to Planner (review progress)
                """
                if not messages:
                    return None

                last_message = messages[-1]

                # If PlanningAgent just spoke
                if last_message.source == "Planner":
                    # Let the LLM selector choose between Coder/CodeSearcher
                    return None  # None = use default LLM selector

                # If Coder or CodeSearcher acted, ALWAYS return to Planner
                # so it can review progress and update the plan
                if last_message.source in ["Coder", "CodeSearcher"]:
                    return "Planner"

                # For other cases, use default selector
                return None

            # Create complex team with selector_func
            termination = TextMentionTermination("TASK_COMPLETED") | MaxMessageTermination(15)

            complex_team = SelectorGroupChat(
                participants=[
                    self.planning_agent,
                    self.coder_agent,
                ],
                model_client=self.router_client,
                termination_condition=termination,
                selector_func=custom_selector_func,  # ← Key for re-planning
            )

            # Execute with streaming
            self.logger.debug("Starting SelectorGroupChat with streaming...")

            agent_messages_shown = set()
            message_count = 0
            spinner_active = False

            # Start initial spinner
            self.cli.start_thinking(message="starting planning")
            spinner_active = True

            async for msg in complex_team.run_stream(task=user_input):
                message_count += 1
                msg_type = type(msg).__name__

                if hasattr(msg, "source") and msg.source != "user":
                    agent_name = msg.source

                    if hasattr(msg, "content"):
                        content = msg.content
                    else:
                        content = str(msg)

                    # Crear clave única
                    try:
                        content_str = str(content) if isinstance(content, list) else content
                        message_key = f"{agent_name}:{hash(content_str)}"
                    except TypeError:
                        message_key = f"{agent_name}:{hash(str(content))}"

                    if message_key not in agent_messages_shown:
                        # Show messages by type
                        if msg_type == "TextMessage":
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            self.cli.print_agent_message(content_str, agent_name)
                            self.logger.debug(f"[{agent_name}] {content_str[:100]}")
                            agent_messages_shown.add(message_key)

                            # After agent finishes, start spinner waiting for next agent
                            self.cli.start_thinking(message="waiting for next action")
                            spinner_active = True

                        elif msg_type == "ToolCallRequestEvent":
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)

                            if isinstance(content, list):
                                tool_names = []
                                for tool_call in content:
                                    if hasattr(tool_call, "name"):
                                        tool_name = tool_call.name
                                        self.cli.print_info(
                                            f"🔧 Executing: {tool_name}", agent_name
                                        )
                                        tool_names.append(tool_name)

                                # Restart spinner ONCE with first tool name (not in loop)
                                if tool_names:
                                    self.cli.start_thinking(message=f"executing {tool_names[0]}")
                                    spinner_active = True
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallExecutionEvent":
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            if isinstance(content, list):
                                for result in content:
                                    if hasattr(result, "name"):
                                        tool_name = result.name
                                        result_content = (
                                            str(result.content)
                                            if hasattr(result, "content")
                                            else "OK"
                                        )

                                        # Check if this is an edit_file result with diff
                                        if (
                                            tool_name == "edit_file"
                                            and "DIFF (Changes Applied)" in result_content
                                        ):
                                            # Extract and display the diff
                                            diff_start = result_content.find(
                                                "═══════════════════════════════════════════════════════════════\n📋 DIFF (Changes Applied):"
                                            )
                                            diff_end = result_content.find(
                                                "\n═══════════════════════════════════════════════════════════════",
                                                diff_start + 100,
                                            )

                                            if diff_start != -1 and diff_end != -1:
                                                diff_text = result_content[
                                                    diff_start : diff_end + 64
                                                ]
                                                # Print file info first
                                                info_end = result_content.find(
                                                    "\n\n", 0, diff_start
                                                )
                                                if info_end != -1:
                                                    file_info = result_content[:info_end]
                                                    self.cli.print_thinking(
                                                        f"✅ {tool_name}: {file_info}"
                                                    )
                                                # Display diff with colors
                                                self.cli.print_diff(diff_text)
                                            else:
                                                # Fallback to showing preview
                                                result_preview = result_content[:100]
                                                self.cli.print_thinking(
                                                    f"✅ {tool_name}: {result_preview}..."
                                                )
                                        else:
                                            # Regular tool result
                                            result_preview = result_content[:100]
                                            self.cli.print_thinking(
                                                f"✅ {tool_name}: {result_preview}..."
                                            )

                            self.cli.start_thinking()
                            spinner_active = True
                            agent_messages_shown.add(message_key)

            # Ensure spinner is stopped
            if spinner_active:
                self.cli.stop_thinking(clear=True)

            # Stop task tracking panel
            if self.cli.task_panel_active:
                self.cli.stop_task_tracking()

            self.logger.info("✅ Complex flow completed")
            self.cli.print_success("\n✅ Complex task completed!")

            # 💾 AUTO-SAVE: Save agent states automatically after each response
            await self._auto_save_agent_states()

        except Exception as e:
            if spinner_active:
                self.cli.stop_thinking(clear=True)
            # Stop task tracking on error
            if self.cli.task_panel_active:
                self.cli.stop_task_tracking()
            self.logger.log_error_with_context(e, "_execute_complex_task")
            self.cli.print_error(f"Error in complex task: {str(e)}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")

    # =========================================================================
    # USER REQUEST PROCESSING
    # =========================================================================

    async def process_user_request(self, user_input: str):
        """
        Process a user request using the single ROUTER TEAM.

        NEW ARCHITECTURE (SIMPLIFIED):
        - Single SelectorGroupChat (self.main_team) that routes automatically
        - The LLM router decides which agent to use based on context
        - No more manual complexity detection
        - No more team recreation
        - The team persists and handles everything automatically

        AVAILABLE AGENTS IN THE ROUTER:
        - Planner: Complex multi-step tasks
        - CodeSearcher: Code search and analysis
        - Coder: Direct code modifications
        """
        try:
            self.logger.info(f"📝 New user request: {user_input[:100]}...")

            # ============= START JSON LOGGING SESSION =============
            # Capture ALL interactions in JSON (independent of Langfuse)
            self.json_logger.start_session(
                mode=self.current_mode, model=self.settings.model, base_url=self.settings.base_url
            )
            self.json_logger.log_user_message(
                content=user_input,
                mentioned_files=(
                    [str(f) for f in self.cli.mentioned_files] if self.cli.mentioned_files else []
                ),
            )

            # Check if there are mentioned files and add their context
            mentioned_files_content = ""
            if self.cli.mentioned_files:
                self.cli.print_mentioned_files()
                mentioned_files_content = self.cli.get_mentioned_files_content()
                self.logger.info(
                    f"📎 Including {len(self.cli.mentioned_files)} mentioned file(s) in context"
                )

            # =================================================================
            # DYNAMIC SKILL RAG INJECTION (SEMANTIC THRESHOLD-BASED)
            # =================================================================
            # Skills are automatically injected ONLY if their semantic similarity
            # score with the query exceeds the threshold (default: 0.6).
            #
            # This prevents false positives where irrelevant skills activate
            # (e.g., xlsx/pptx skills activating on "summarize the project").
            #
            # The RAGManager uses:
            # - Multi-Query Generation (query variations)
            # - Reciprocal Rank Fusion (combines multiple results)
            # - Score threshold filtering (min_score parameter)
            # =================================================================
            relevant_skills = self.skill_manager.find_relevant_skills(
                user_input,
                max_results=3,      # Maximum skills to activate
                min_score=0.6       # Minimum semantic similarity (0.0-1.0)
                                    # 0.6 = moderately relevant (strict enough to avoid false positives)
                                    # Lower = more permissive, higher = stricter matching
            )
            skills_context = ""

            if relevant_skills:
                skills_list = "\n".join([s.to_context_string() for s in relevant_skills])
                skills_context = f"\n\n<active_skills>\nThe following skills are relevant to your request and available for use:\n\n{skills_list}\n</active_skills>"
                self.logger.info(f"🧠 RAG activated {len(relevant_skills)} relevant skill(s): {[s.name for s in relevant_skills]}")
            else:
                self.logger.debug("🧠 No skills met the relevance threshold for this request")

            # Prepare final input with context
            # Combine: User Request + Mentioned Files + Skills Context
            full_input = f"{user_input}\n{mentioned_files_content}{skills_context}"

            self.logger.debug(f"Input context prepared with {len(skills_context)} chars of skills")

            # =================================================================
            # DYNAMIC COMPLEXITY DETECTION & MODEL SWITCHING
            # =================================================================
            # Detect complexity to choose the right model for the Coder
            complexity = await self._detect_task_complexity(full_input)

            # Switch Coder model based on complexity
            if complexity == "complex":
                # Use Strong Model (Reasoner)
                self.coder_agent._model_client._wrapped = self.client_strong
                model_name = self.settings.strong_model
                self.logger.info(f"🧠 Task is COMPLEX: Switched Coder to Strong Model ({model_name})")
            else:
                # Use Base Model (Standard)
                self.coder_agent._model_client._wrapped = self.client_base
                model_name = self.settings.base_model
                self.logger.info(f"⚡ Task is SIMPLE: Switched Coder to Base Model ({model_name})")

            # ============= USE SINGLE ROUTER TEAM =============

            # Start spinner
            self.cli.start_thinking()

            agent_messages_shown = set()
            message_count = 0
            spinner_active = True

            # Track for logging
            all_agent_responses = []
            agents_used = []
            tools_called = []

            # Process messages with streaming using the ROUTER TEAM
            async for msg in self.main_team.run_stream(task=full_input):
                message_count += 1
                msg_type = type(msg).__name__
                self.logger.debug(f"Stream mensaje #{message_count} - Tipo: {msg_type}")

                # Only process messages that are NOT from the user
                if hasattr(msg, "source") and msg.source != "user":
                    agent_name = msg.source

                    # Track which agents were used
                    if agent_name not in agents_used:
                        agents_used.append(agent_name)

                    # Determine message content
                    if hasattr(msg, "content"):
                        content = msg.content
                    else:
                        content = str(msg)
                        self.logger.warning(
                            f"Message without 'content' attribute. Using str(): {content[:100]}..."
                        )

                    # Create unique key to avoid duplicates
                    # If content is a list (e.g. FunctionCall), convert to string
                    try:
                        if isinstance(content, list):
                            content_str = str(content)
                        else:
                            content_str = content
                        message_key = f"{agent_name}:{hash(content_str)}"
                    except TypeError:
                        # If still can't hash, use hash of string
                        message_key = f"{agent_name}:{hash(str(content))}"

                    if message_key not in agent_messages_shown:
                        # SHOW DIFFERENT MESSAGE TYPES IN CONSOLE IN REAL-TIME
                        if msg_type == "ThoughtEvent":
                            # 💭 Show agent thoughts/reflections
                            # Stop spinner for thoughts to show them clearly
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False
                            self.cli.print_thinking(f"💭 {agent_name}: {content_str}")
                            self.logger.debug(f"💭 Thought: {content_str}")
                            # JSON Logger: Capture thought
                            self.json_logger.log_thought(agent_name, content_str)
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallRequestEvent":
                            # 🔧 Show tools to be called
                            # Stop spinner to show tool call, then restart with specific message
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)

                            if isinstance(content, list):
                                tool_names = []
                                for tool_call in content:
                                    if hasattr(tool_call, "name"):
                                        tool_name = tool_call.name
                                        tool_args = (
                                            tool_call.arguments
                                            if hasattr(tool_call, "arguments")
                                            else {}
                                        )

                                        # Parse tool_args if it's a JSON string
                                        if isinstance(tool_args, str):
                                            try:
                                                import json
                                                tool_args = json.loads(tool_args)
                                            except (json.JSONDecodeError, TypeError):
                                                pass  # Keep as string if parsing fails

                                        # Special formatting for file tools with code content
                                        if tool_name == "write_file" and isinstance(tool_args, dict) and "file_content" in tool_args:
                                            # Show write_file with syntax highlighting
                                            target_file = tool_args.get("target_file", "unknown")
                                            file_content = tool_args.get("file_content", "")
                                            self.cli.print_thinking(f"🔧 {agent_name} > {tool_name}: Writing to {target_file}")
                                            self.cli.print_code(file_content, target_file, max_lines=50)
                                        elif tool_name == "edit_file" and isinstance(tool_args, dict):
                                            # Show edit_file with unified diff
                                            import difflib
                                            target_file = tool_args.get("target_file", "unknown")
                                            old_string = tool_args.get("old_string", "")
                                            new_string = tool_args.get("new_string", "")
                                            instructions = tool_args.get("instructions", "")
                                            self.cli.print_thinking(f"🔧 {agent_name} > {tool_name}: Editing {target_file}")
                                            if instructions:
                                                self.cli.print_thinking(f"   📝 {instructions}")
                                            # Generate unified diff
                                            old_lines = old_string.splitlines(keepends=True)
                                            new_lines = new_string.splitlines(keepends=True)
                                            diff = difflib.unified_diff(
                                                old_lines, new_lines,
                                                fromfile=f"a/{target_file}",
                                                tofile=f"b/{target_file}",
                                                lineterm=""
                                            )
                                            diff_text = "".join(diff)
                                            if diff_text:
                                                self.cli.print_diff(diff_text)
                                            else:
                                                self.cli.print_thinking("   (no changes detected in diff)")
                                        else:
                                            # Default: show parameters as JSON (truncate if too long)
                                            args_str = str(tool_args)
                                            if len(args_str) > 200:
                                                args_str = args_str[:200] + "..."
                                            self.cli.print_info(
                                                f"🔧 Calling tool: {tool_name} with parameters {args_str}",
                                                agent_name,
                                            )

                                        self.logger.debug(f"🔧 Tool call: {tool_name}")
                                        # JSON Logger: Capture tool call
                                        self.json_logger.log_tool_call(
                                            agent_name=agent_name,
                                            tool_name=tool_name,
                                            arguments=(
                                                tool_args if isinstance(tool_args, dict) else {}
                                            ),
                                        )
                                        # Track tools called
                                        if tool_name not in tools_called:
                                            tools_called.append(tool_name)
                                        tool_names.append(tool_name)

                                # Restart spinner ONCE with first tool name (not in loop)
                                if tool_names:
                                    self.logger.debug(f"executing {tool_names[0]}")
                                    spinner_active = True
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallExecutionEvent":
                            # ✅ Show tool results
                            # Stop spinner to show results
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            if isinstance(content, list):
                                for execution_result in content:
                                    if hasattr(execution_result, "name"):
                                        tool_name = execution_result.name
                                        result_content = (
                                            str(execution_result.content)
                                            if hasattr(execution_result, "content")
                                            else "OK"
                                        )

                                        # DEBUG: Log tool result details
                                        self.logger.debug(f"[TOOL_RESULT_DEBUG] tool_name={tool_name}, result_starts_with={result_content[:50] if len(result_content) > 50 else result_content}, has_File={('File:' in result_content)}")

                                        # Check if this is an edit_file result with diff
                                        if (
                                            tool_name == "edit_file"
                                            and "DIFF (Changes Applied)" in result_content
                                        ):
                                            # Extract and display the diff
                                            diff_start = result_content.find(
                                                "═══════════════════════════════════════════════════════════════\n📋 DIFF (Changes Applied):"
                                            )
                                            diff_end = result_content.find(
                                                "\n═══════════════════════════════════════════════════════════════",
                                                diff_start + 100,
                                            )

                                            if diff_start != -1 and diff_end != -1:
                                                diff_text = result_content[
                                                    diff_start : diff_end + 64
                                                ]
                                                # Print file info first
                                                info_end = result_content.find(
                                                    "\n\n", 0, diff_start
                                                )
                                                if info_end != -1:
                                                    file_info = result_content[:info_end]
                                                    self.cli.print_thinking(
                                                        f"✅ {agent_name} > {tool_name}: {file_info}"
                                                    )
                                                # Display diff with colors
                                                self.cli.print_diff(diff_text)
                                                self.logger.debug(
                                                    f"✅ Tool result: {tool_name} -> DIFF displayed"
                                                )
                                            else:
                                                # Fallback to showing preview
                                                result_preview = result_content[:100]
                                                self.cli.print_thinking(
                                                    f"✅ {agent_name} > {tool_name}: {result_preview}..."
                                                )
                                                self.logger.debug(
                                                    f"✅ Tool result: {tool_name} -> {result_preview}"
                                                )
                                        elif tool_name == "read_file" and "File:" in result_content:
                                            # Special handling for read_file - show with syntax highlighting
                                            # Extract filename from result
                                            try:
                                                # Result format: "File: <path>\n<content>"
                                                first_line = result_content.split("\n")[0]
                                                if first_line.startswith("File:"):
                                                    filename = first_line.replace("File:", "").strip()
                                                    # Get code content (everything after first line)
                                                    code_content = "\n".join(result_content.split("\n")[1:])
                                                    # Display with syntax highlighting
                                                    self.cli.print_code(code_content, filename, max_lines=50)
                                                    self.logger.debug(f"✅ Tool result: {tool_name} -> {filename} (displayed with syntax highlighting)")
                                                else:
                                                    # Fallback
                                                    result_preview = result_content[:100]
                                                    self.cli.print_thinking(f"✅ {agent_name} > {tool_name}: {result_preview}...")
                                            except Exception:
                                                result_preview = result_content[:100]
                                                self.cli.print_thinking(f"✅ {agent_name} > {tool_name}: {result_preview}...")
                                        elif tool_name == "write_file" and "Successfully wrote" in result_content:
                                            # Special handling for write_file - show success message
                                            self.cli.print_success(f"{agent_name} > {tool_name}: {result_content}")
                                            self.logger.debug(f"✅ Tool result: {tool_name} -> {result_content}")
                                        else:
                                            # Regular tool result
                                            result_preview = result_content[:100]
                                            self.cli.print_thinking(
                                                f"✅ {agent_name} > {tool_name}: {result_preview}..."
                                            )
                                            self.logger.debug(
                                                f"✅ Tool result: {tool_name} -> {result_preview}"
                                            )

                                        # JSON Logger: Capture tool result
                                        self.json_logger.log_tool_result(
                                            agent_name=agent_name,
                                            tool_name=tool_name,
                                            result=result_content,
                                            success=True,
                                        )

                            # Restart spinner for next action
                            self.cli.start_thinking()
                            spinner_active = True
                            agent_messages_shown.add(message_key)

                        elif msg_type == "TextMessage":
                            # 💬 Show final agent response
                            # Stop spinner for final response
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            preview = content_str[:100] if len(content_str) > 100 else content_str
                            self.logger.log_message_processing(msg_type, agent_name, preview)
                            self.cli.print_agent_message(content_str, agent_name)
                            # JSON Logger: Capture agent message
                            self.json_logger.log_agent_message(
                                agent_name=agent_name, content=content_str, message_type="text"
                            )
                            # Collect agent responses for logging
                            all_agent_responses.append(f"[{agent_name}] {content_str}")
                            agent_messages_shown.add(message_key)

                            # After agent finishes, start spinner waiting for next agent
                            self.cli.start_thinking(message="waiting for next action")
                            spinner_active = True

                        else:
                            # Other message types (for debugging)
                            self.logger.debug(f"Message type {msg_type} not shown in CLI")

            self.logger.debug(f"✅ Stream completed. Total messages processed: {message_count}")

            # Ensure spinner is stopped
            self.cli.stop_thinking()

            # Log interaction to JSON
            self._log_interaction_to_json(
                user_input=user_input,
                agent_responses=all_agent_responses,
                agents_used=agents_used,
                tools_called=tools_called,
            )

            # Generate task completion summary
            await self._generate_task_summary(user_input)

            # 💾 AUTO-SAVE: Save agent states automatically after each response
            await self._auto_save_agent_states()

            # ============= END JSON LOGGING SESSION =============
            # Save all captured events to timestamped JSON file
            self.json_logger.end_session(summary="Request completed successfully")

        except Exception as e:
            # Stop spinner on error
            self.cli.stop_thinking()

            # JSON Logger: Capture error
            self.json_logger.log_error(e, context="process_user_request")
            self.json_logger.end_session(summary=f"Request failed with error: {str(e)}")

            self.logger.log_error_with_context(e, "process_user_request")
            self.cli.print_error(f"Error processing request: {str(e)}")
            import traceback

            error_traceback = traceback.format_exc()
            self.logger.error(f"Full traceback:\n{error_traceback}")
            self.logger.error(f"Full traceback:\n{error_traceback}")
            self.cli.print_error(f"Details:\n{error_traceback}")

            # AUTOMATIC ERROR REPORTING TO SIGNOZ
            self.cli.print_thinking("📊 Reporting error to SigNoz...")
            try:
                await self.error_reporter.report_error(
                    exception=e,
                    context="process_user_request",
                    severity="error"
                )
            except Exception as report_err:
                self.logger.error(f"Failed to report error: {report_err}")

    # =========================================================================
    # CONVERSATION TRACKING - Log to JSON
    # =========================================================================

    def _log_interaction_to_json(
        self, user_input: str, agent_responses: list, agents_used: list, tools_called: list
    ):
        """
        Log the interaction with the LLM to JSON file and vector memory

        Args:
            user_input: User's request
            agent_responses: List of agent responses
            agents_used: List of participating agents
            tools_called: List of tools called
        """
        try:
            # Combine all agent responses
            combined_response = "\n\n".join(agent_responses) if agent_responses else "No response"

            # Determine provider from base URL
            provider = "unknown"
            if "deepseek" in self.settings.base_url.lower():
                provider = "DeepSeek"
            elif "openai" in self.settings.base_url.lower():
                provider = "OpenAI"
            elif "anthropic" in self.settings.base_url.lower():
                provider = "Anthropic"

            # Log the interaction to JSON file
            interaction_id = self.conversation_tracker.log_interaction(
                user_request=user_input,
                agent_response=combined_response,
                model=self.settings.model,
                provider=provider,
                agent_name="DaveAgent",
                metadata={
                    "agents_used": agents_used,
                    "tools_called": tools_called,
                    "total_agents": len(agents_used),
                    "total_tools": len(tools_called),
                },
            )

            self.logger.debug(f"📝 Interaction logged to JSON with ID: {interaction_id}")

        except Exception as e:
            self.logger.error(f"Error logging interaction to JSON: {str(e)}")
            # Don't fail the whole request if logging fails

    # =========================================================================
    # TASK SUMMARY - Completed task summary
    # =========================================================================

    async def _generate_task_summary(self, original_request: str):
        """
        Display task completed message
        (Simplified - no longer uses SummaryAgent)

        Args:
            original_request: User's original request
        """
        try:
            self.logger.info("✅ Task completed")
            self.cli.print_success("\n✅ Task completed successfully.")
        except Exception as e:
            self.logger.error(f"Error showing summary: {str(e)}")
            # Fail silently with default message
            self.cli.print_success("\n✅ Task completed.")

    # =========================================================================
    # UNCHANGED FUNCTIONS
    # =========================================================================

    async def _check_and_resume_session(self):
        """
        Check for previous sessions and offer to resume the most recent one
        """
        try:
            sessions = self.state_manager.list_sessions()

            if not sessions:
                # No previous sessions, start fresh
                self.logger.info("No previous sessions, starting new session")
                return

            # Get most recent session
            latest_session = sessions[0]
            session_id = latest_session.get("session_id")
            title = latest_session.get("title", "Untitled")
            total_messages = latest_session.get("total_messages", 0)
            last_interaction = latest_session.get("last_interaction", "")

            # Format date
            if last_interaction:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(last_interaction)
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = last_interaction
            else:
                formatted_date = "Unknown"

            # Display session info
            self.cli.print_info(f"\n Previous session found: Messages: {total_messages}")

            # Prompt user (use async prompt)
            from prompt_toolkit import PromptSession
            from prompt_toolkit.patch_stdout import patch_stdout

            session = PromptSession()
            with patch_stdout():
                response = await session.prompt_async(
                    "\nDo you want to continue with this session? (Y/n): "
                )
            response = response.strip().lower()

            if response in ["s", "si", "sí", "yes", "y", ""]:
                # Load the session
                self.cli.print_info(f"\n📂 Loading session: {title}...")

                # Load state
                loaded = await self.state_manager.load_from_disk(session_id)

                if loaded:
                    # Load agents
                    agents_loaded = 0
                    if await self.state_manager.load_agent_state("coder", self.coder_agent):
                        agents_loaded += 1

                    if await self.state_manager.load_agent_state("planning", self.planning_agent):
                        agents_loaded += 1

                    # Get metadata and messages
                    metadata = self.state_manager.get_session_metadata()
                    messages = self.state_manager.get_session_history()

                    # Display success
                    self.cli.print_success(f"\n✅ Session loaded: {title}")
                    self.cli.print_info(f"  • Messages restored: {len(messages)}")
                    self.cli.print_info(f"  • Agents restored: {agents_loaded}")

                    # Show last few messages
                    if messages:
                        self.cli.print_info("\n📜 Recent messages:")
                        if self.history_viewer:
                            self.history_viewer.display_conversation_history(
                                messages=messages,
                                max_messages=5,  # Show last 5 messages
                                show_thoughts=False,
                            )

                        if len(messages) > 5:
                            self.cli.print_info(
                                f"💡 Use /history to see all {len(messages)} messages"
                            )

                    self.cli.print_info("\n✅ You can continue the conversation\n")
                else:
                    self.cli.print_error("Error loading session")
            else:
                self.cli.print_info("\n✨ Starting new session")
                self.cli.print_info("💡 Use /new-session <title> to create a named session\n")

        except Exception as e:
            self.logger.error(f"Error checking previous sessions: {e}")
            # Continue without loading session

    async def run(self):
        """Execute the main CLI loop"""
        self.cli.print_banner()

        # Check for previous sessions and offer to resume
        await self._check_and_resume_session()

        try:
            while self.running:
                user_input = await self.cli.get_user_input()

                if not user_input:
                    continue

                self.logger.debug(f"Input received: {user_input[:100]}")
                self.cli.print_user_message(user_input)

                if user_input.startswith("/"):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        self.logger.info("👋 User requested exit")
                        break
                    continue

                await self.process_user_request(user_input)

        except KeyboardInterrupt:
            self.logger.warning("⚠️ Keyboard interrupt (Ctrl+C)")
            self.cli.print_warning("\nInterrupted by user")

        except Exception as e:
            self.logger.log_error_with_context(e, "main loop")
            self.cli.print_error(f"Fatal error: {str(e)}")

            # AUTOMATIC ERROR REPORTING FOR FATAL ERRORS
            try:
                await self.error_reporter.report_error(
                    exception=e,
                    context="main_loop_fatal_error",
                    severity="critical"
                )
            except Exception as report_err:
                self.logger.error(f"Failed to report fatal error: {report_err}")

        finally:
            self.logger.info("🔚 Closing DaveAgent CLI")
            self.cli.print_goodbye()

            # Close state system (saves final state automatically)
            try:
                await self.state_manager.close()
            except Exception as e:
                self.logger.error(f"Error closing state: {e}")

            # Langfuse: OpenLit does automatic flush on exit
            if self.langfuse_enabled:
                self.logger.info("� Langfuse: data sent automatically by OpenLit")




async def main(
    debug: bool = False,
    api_key: str = None,
    base_url: str = None,
    model: str = None,
    ssl_verify: bool = None,
    vscode_mode: bool = False,
):
    """
    Main entry point

    Args:
        debug: If True, enable debug mode with detailed logging
        api_key: API key for the LLM model
        base_url: Base URL of the API
        model: Name of the model to use
        ssl_verify: Whether to verify SSL certificates (default True)
    """
    app = DaveAgentCLI(
        debug=debug,
        api_key=api_key,
        base_url=base_url,
        model=model,
        ssl_verify=ssl_verify,
        vscode_mode=vscode_mode,
    )
    await app.run()


if __name__ == "__main__":
    import sys

    # Detect if --debug flag was passed
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    if debug_mode:
        print("🐛 DEBUG mode enabled")

    asyncio.run(main(debug=debug_mode))
