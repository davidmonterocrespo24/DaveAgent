"""
Main file - Complete CLI interface for the code agent
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="autogen.import_utils")
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, module="chromadb.api.collection_configuration"
)

import asyncio
import logging
import os
import signal
import sys

# Ensure we use local src files over installed packages
sys.path.insert(0, os.getcwd())

# Import the orchestrator that handles all agent initialization
from src.config.orchestrator import AgentOrchestrator
from src.utils.errors import UserCancelledError


class DaveAgentCLI(AgentOrchestrator):
    """Main CLI application for the code agent - extends AgentOrchestrator"""

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
        Initialize all agent components by calling parent AgentOrchestrator
        """
        import time

        t_start = time.time()

        # Initialize the orchestrator (handles all agent setup)
        super().__init__(
            debug=debug,
            api_key=api_key,
            base_url=base_url,
            model=model,
            ssl_verify=ssl_verify,
            headless=headless,
        )
        print(f"[Startup] Model clients initialized in {time.time() - t_start:.4f}s")
        self.should_exit = False

        t0 = time.time()
        # State management system (AutoGen save_state/load_state)
        from src.managers import StateManager

        _state_dir = os.path.join(os.getcwd(), ".daveagent", "state")
        print(f"[Startup] Working directory: {os.getcwd()}")
        print(f"[Startup] State directory: {_state_dir}")
        self.state_manager = StateManager(
            auto_save_enabled=True,
            auto_save_interval=300,  # Auto-save every 5 minutes
            state_dir=_state_dir,
        )
        print(f"[Startup] StateManager initialized in {time.time() - t0:.4f}s")

        t0 = time.time()
        # Agent Skills system
        from src.skills import SkillManager

        self.skill_manager = SkillManager(logger=self.logger.logger)
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
        import threading

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

    # =========================================================================
    # COMMAND HANDLING
    # =========================================================================

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
                self.cli.print_info(
                    "Edit this file to add project-specific commands and guidelines."
                )
            except Exception as e:
                self.cli.print_error(f"Error creating DAVEAGENT.md: {e}")

        # REMOVED: /load command - Use /load-state instead (AutoGen official)

        elif cmd == "/debug":
            # Change console handler level (file handler always stays at DEBUG)
            console_handlers = [h for h in self.logger.logger.handlers if isinstance(h, logging.Handler) and not isinstance(h, logging.FileHandler)]
            current_console_level = console_handlers[0].level if console_handlers else logging.INFO
            if current_console_level == logging.DEBUG:
                for h in console_handlers:
                    h.setLevel(logging.INFO)
                self.cli.print_success("🔧 Debug mode DISABLED (console: INFO, file: DEBUG)")
                self.logger.info("Console logging level changed to INFO")
            else:
                for h in console_handlers:
                    h.setLevel(logging.DEBUG)
                self.cli.print_success("🐛 Debug mode ENABLED (console: DEBUG, file: DEBUG)")
                self.logger.debug("Console logging level changed to DEBUG")

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

        elif cmd == "/subagents":
            # List active subagents
            await self._list_subagents_command()

        elif cmd == "/subagent-status":
            # Show status of specific subagent
            if len(parts) < 2:
                self.cli.print_error("Usage: /subagent-status <subagent-id>")
                self.cli.print_info("Use /subagents to see active subagents")
            else:
                await self._subagent_status_command(parts[1])

        elif cmd == "/cron":
            # Cron management commands
            if len(parts) < 2:
                self.cli.print_error("Usage: /cron <add|list|enable|disable|remove|run>")
                self.cli.print_info("Examples:")
                self.cli.print_info("  /cron add at 2026-02-20T15:30 Review PRs")
                self.cli.print_info("  /cron add every 1h Check build status")
                self.cli.print_info("  /cron add cron '0 9 * * *' Daily standup")
                self.cli.print_info("  /cron list")
                self.cli.print_info("  /cron enable <job-id>")
                self.cli.print_info("  /cron run <job-id>")
            else:
                subcmd = parts[1]
                await self._cron_command(subcmd, parts[2:])

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
                    desc = (
                        skill.description[:60] + "..."
                        if len(skill.description) > 60
                        else skill.description
                    )
                    self.cli.print_info(f"  • {skill.name}: {desc}")

            if project_skills:
                self.cli.print_info("\n📂 Project Skills:")
                for skill in project_skills:
                    desc = (
                        skill.description[:60] + "..."
                        if len(skill.description) > 60
                        else skill.description
                    )
                    self.cli.print_info(f"  • {skill.name}: {desc}")

            if plugin_skills:
                self.cli.print_info("\n🔌 Plugin Skills:")
                for skill in plugin_skills:
                    desc = (
                        skill.description[:60] + "..."
                        if len(skill.description) > 60
                        else skill.description
                    )
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

            # Save team state
            self.logger.debug(f"💾 Auto-save: saving team state, session={self.state_manager.session_id}")
            await self.state_manager.save_agent_state(
                "Coder", self.coder_agent, metadata={"description": "Main coder agent with tools"}
            )

            await self.state_manager.save_agent_state(
                "Planner",
                self.planning_agent,
                metadata={"description": "Planning and task management agent"},
            )

            # Save to disk
            await self.state_manager.save_to_disk()

            # Save session metadata to disk
            await self.state_manager.save_to_disk()

            

        except Exception as e:
            # Don't fail if auto-save fails, just log
            import traceback
            self.logger.warning(f"⚠️ Auto-save failed: {str(e)}\n{traceback.format_exc()}")

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

            # Save team state
            await self.state_manager.save_team_state(self.main_team, self.client_strong)

            # Save session metadata to disk
            state_path = await self.state_manager.save_to_disk(session_id)

            self.cli.stop_thinking()

            # Get metadata and messages for display
            metadata = self.state_manager.get_session_metadata()
            messages = self.state_manager.get_session_history()

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

            # Load team state
            team_loaded = await self.state_manager.load_team_state(self.main_team, self.client_strong)

            self.cli.stop_thinking()

            # Get session metadata and history
            metadata = self.state_manager.get_session_metadata()
            messages = self.state_manager.get_session_history()

            # Display session info
            if self.history_viewer:
                self.history_viewer.display_session_loaded(
                    session_id=session_id,
                    total_messages=len(messages),
                    agents_restored=1 if team_loaded else 0,
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

    async def _list_subagents_command(self):
        """
        Command /subagents: List all active subagents

        Shows currently running subagents with their IDs, labels, and status.
        """
        try:
            if not hasattr(self.orchestrator, 'subagent_manager'):
                self.cli.print_warning("Subagent system not initialized")
                return

            manager = self.subagent_manager
            running_tasks = manager._running_tasks

            if not running_tasks:
                self.cli.print_info("No active subagents")
                return

            # Create table data
            from rich.table import Table
            from rich import box

            table = Table(
                title="[bold cyan]Active Subagents[/bold cyan]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Status", style="yellow")
            table.add_column("Started", style="dim")

            # Get event history to find labels and start times
            event_bus = manager.event_bus
            spawned_events = [e for e in event_bus._event_history if e.event_type == "spawned"]

            for subagent_id, task in running_tasks.items():
                status = "Running" if not task.done() else "Completed"

                # Find spawn event for this subagent
                spawn_event = next((e for e in spawned_events if e.subagent_id == subagent_id), None)
                if spawn_event:
                    from datetime import datetime
                    start_time = datetime.fromtimestamp(spawn_event.timestamp).strftime("%H:%M:%S")
                else:
                    start_time = "Unknown"

                table.add_row(subagent_id, status, start_time)

            self.cli.console.print()
            self.cli.console.print(table)
            self.cli.console.print()
            self.cli.print_info(f"Total active subagents: {len(running_tasks)}")
            self.cli.print_info("Use /subagent-status <id> to see detailed status")

        except Exception as e:
            self.logger.log_error_with_context(e, "_list_subagents_command")
            self.cli.print_error(f"Error listing subagents: {str(e)}")

    async def _subagent_status_command(self, subagent_id: str):
        """
        Command /subagent-status: Show detailed status of a specific subagent

        Args:
            subagent_id: The ID of the subagent to check
        """
        try:
            if not hasattr(self.orchestrator, 'subagent_manager'):
                self.cli.print_warning("Subagent system not initialized")
                return

            manager = self.subagent_manager

            # Check if subagent exists
            if subagent_id not in manager._running_tasks and subagent_id not in manager._results:
                self.cli.print_error(f"Subagent '{subagent_id}' not found")
                self.cli.print_info("Use /subagents to see active subagents")
                return

            # Get all events for this subagent
            event_bus = manager.event_bus
            subagent_events = [e for e in event_bus._event_history if e.subagent_id == subagent_id]

            if not subagent_events:
                self.cli.print_warning(f"No events found for subagent '{subagent_id}'")
                return

            # Display subagent information
            from rich.panel import Panel
            from rich.markdown import Markdown
            from datetime import datetime

            # Get spawn event
            spawn_event = next((e for e in subagent_events if e.event_type == "spawned"), None)
            if spawn_event:
                label = spawn_event.content.get('label', 'Unknown')
                task = spawn_event.content.get('task', 'Unknown')
                start_time = datetime.fromtimestamp(spawn_event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            else:
                label = "Unknown"
                task = "Unknown"
                start_time = "Unknown"

            # Check status
            is_running = subagent_id in manager._running_tasks
            has_result = subagent_id in manager._results

            # Get completion/failure info
            completed_event = next((e for e in subagent_events if e.event_type == "completed"), None)
            failed_event = next((e for e in subagent_events if e.event_type == "failed"), None)

            if completed_event:
                status = "Completed"
                end_time = datetime.fromtimestamp(completed_event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                result = completed_event.content.get('result', 'No result')
                result_preview = result[:200] + "..." if len(result) > 200 else result
            elif failed_event:
                status = "Failed"
                end_time = datetime.fromtimestamp(failed_event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                result_preview = f"Error: {failed_event.content.get('error', 'Unknown error')}"
            elif is_running:
                status = "Running"
                end_time = "N/A"
                result_preview = "Still executing..."
            else:
                status = "Unknown"
                end_time = "N/A"
                result_preview = "No result available"

            # Create markdown content
            status_text = f"""
**Subagent Status Report**

**ID:** `{subagent_id}`
**Label:** {label}
**Status:** {status}
**Started:** {start_time}
**Ended:** {end_time}

**Task:**
```
{task}
```

**Result:**
```
{result_preview}
```

**Events:** {len(subagent_events)} total
            """

            self.cli.console.print()
            self.cli.console.print(
                Panel(
                    Markdown(status_text),
                    title=f"[bold cyan]Subagent {subagent_id}[/bold cyan]",
                    border_style="cyan"
                )
            )
            self.cli.console.print()

        except Exception as e:
            self.logger.log_error_with_context(e, "_subagent_status_command")
            self.cli.print_error(f"Error showing subagent status: {str(e)}")

    # =========================================================================
    # CRON MANAGEMENT
    # =========================================================================

    async def _cron_command(self, subcmd: str, args: list):
        """Handle cron subcommands."""
        if not hasattr(self, 'cron_service') or self.cron_service is None:
            self.cli.print_error("Cron service not initialized")
            return

        try:
            if subcmd == "list":
                await self._cron_list_command()
            elif subcmd == "add":
                await self._cron_add_command(args)
            elif subcmd == "enable":
                await self._cron_enable_command(args, enabled=True)
            elif subcmd == "disable":
                await self._cron_enable_command(args, enabled=False)
            elif subcmd == "remove":
                await self._cron_remove_command(args)
            elif subcmd == "run":
                await self._cron_run_command(args)
            else:
                self.cli.print_error(f"Unknown cron command: {subcmd}")
                self.cli.print_info("Use /cron without arguments to see usage")
        except Exception as e:
            self.logger.log_error_with_context(e, f"_cron_command_{subcmd}")
            self.cli.print_error(f"Error in cron command: {str(e)}")

    async def _cron_list_command(self):
        """List all cron jobs."""
        from rich.table import Table

        jobs = self.cron_service.list_jobs()

        if not jobs:
            self.cli.print_info("\n⏰ No cron jobs scheduled")
            self.cli.print_info("\nAdd a job with:")
            self.cli.print_info("  /cron add at 2026-02-20T15:30 Review PRs")
            self.cli.print_info("  /cron add every 1h Check build status")
            self.cli.print_info("  /cron add cron '0 9 * * *' Daily standup")
            return

        table = Table(title=f"\n⏰ Scheduled Cron Jobs ({len(jobs)} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="yellow")
        table.add_column("Enabled", style="green")
        table.add_column("Schedule", style="magenta")
        table.add_column("Next Run", style="blue")
        table.add_column("Runs", justify="right")
        table.add_column("Status")

        for job in jobs:
            enabled = "✓" if job["enabled"] else "✗"
            status_color = "green" if job["last_status"] == "ok" else "red" if job["last_status"] == "error" else "dim"

            table.add_row(
                job["id"],
                job["name"][:30],
                enabled,
                job["schedule"],
                job["next_run"],
                str(job["run_count"]),
                f"[{status_color}]{job['last_status']}[/{status_color}]"
            )

        self.cli.console.print(table)
        self.cli.console.print()

    async def _cron_add_command(self, args: list):
        """Add a new cron job."""
        from src.cron.types import CronSchedule
        from datetime import datetime

        if len(args) < 2:
            self.cli.print_error("Usage: /cron add <at|every|cron> <time/interval/expr> <task>")
            self.cli.print_info("Examples:")
            self.cli.print_info("  /cron add at 2026-02-20T15:30 Review PRs")
            self.cli.print_info("  /cron add every 1h Check build status")
            self.cli.print_info("  /cron add cron '0 9 * * *' Daily standup")
            return

        schedule_type = args[0]

        if schedule_type == "at":
            # Parse: /cron add at 2026-02-20T15:30 Task description
            if len(args) < 3:
                self.cli.print_error("Usage: /cron add at <datetime> <task>")
                self.cli.print_info("Example: /cron add at 2026-02-20T15:30 Review PRs")
                return

            time_str = args[1]
            task = " ".join(args[2:])

            try:
                # Parse datetime
                dt = datetime.fromisoformat(time_str)
                at_ms = int(dt.timestamp() * 1000)

                schedule = CronSchedule(kind="at", at_ms=at_ms)
                job_id = self.cron_service.add_job(
                    name=task[:50],
                    schedule=schedule,
                    task=task
                )

                self.cli.print_success(f"✓ Added one-time job {job_id}")
                self.cli.print_info(f"  Will run at: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                self.cli.print_info(f"  Task: {task}")
            except ValueError as e:
                self.cli.print_error(f"Invalid datetime format: {e}")
                self.cli.print_info("Use ISO format: YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS")

        elif schedule_type == "every":
            # Parse: /cron add every 1h Task description
            if len(args) < 3:
                self.cli.print_error("Usage: /cron add every <interval> <task>")
                self.cli.print_info("Example: /cron add every 1h Check build status")
                self.cli.print_info("Intervals: 30s, 5m, 1h, 2d (s=seconds, m=minutes, h=hours, d=days)")
                return

            interval_str = args[1]
            task = " ".join(args[2:])

            try:
                # Parse interval (e.g., "1h", "30m", "2d")
                import re
                match = re.match(r'^(\d+)([smhd])$', interval_str)
                if not match:
                    raise ValueError("Invalid interval format")

                value = int(match.group(1))
                unit = match.group(2)

                # Convert to milliseconds
                multipliers = {'s': 1000, 'm': 60000, 'h': 3600000, 'd': 86400000}
                every_ms = value * multipliers[unit]

                schedule = CronSchedule(kind="every", every_ms=every_ms)
                job_id = self.cron_service.add_job(
                    name=task[:50],
                    schedule=schedule,
                    task=task
                )

                self.cli.print_success(f"✓ Added recurring job {job_id}")
                self.cli.print_info(f"  Interval: {interval_str}")
                self.cli.print_info(f"  Task: {task}")
            except ValueError as e:
                self.cli.print_error(f"Invalid interval: {e}")
                self.cli.print_info("Use format: <number><unit> where unit is s/m/h/d")
                self.cli.print_info("Examples: 30s, 5m, 1h, 2d")

        elif schedule_type == "cron":
            # Parse: /cron add cron '0 9 * * *' Task description
            if len(args) < 3:
                self.cli.print_error("Usage: /cron add cron '<expression>' <task>")
                self.cli.print_info("Example: /cron add cron '0 9 * * *' Daily standup")
                return

            cron_expr = args[1]
            task = " ".join(args[2:])

            try:
                # Validate cron expression
                from croniter import croniter
                if not croniter.is_valid(cron_expr):
                    raise ValueError("Invalid cron expression")

                schedule = CronSchedule(kind="cron", expr=cron_expr)
                job_id = self.cron_service.add_job(
                    name=task[:50],
                    schedule=schedule,
                    task=task
                )

                # Show next run times
                from croniter import croniter as CronIter
                from datetime import datetime
                now = datetime.now()
                cron = CronIter(cron_expr, now)
                next_3 = [cron.get_next(datetime).strftime('%Y-%m-%d %H:%M') for _ in range(3)]

                self.cli.print_success(f"✓ Added cron job {job_id}")
                self.cli.print_info(f"  Expression: {cron_expr}")
                self.cli.print_info(f"  Task: {task}")
                self.cli.print_info(f"  Next runs: {', '.join(next_3)}")
            except ImportError:
                self.cli.print_error("croniter library not installed")
                self.cli.print_info("Install with: pip install croniter")
            except ValueError as e:
                self.cli.print_error(f"Invalid cron expression: {e}")
                self.cli.print_info("Use standard cron format: '0 9 * * *'")

        else:
            self.cli.print_error(f"Unknown schedule type: {schedule_type}")
            self.cli.print_info("Supported types: at, every, cron")

    async def _cron_enable_command(self, args: list, enabled: bool):
        """Enable or disable a cron job."""
        if len(args) < 1:
            action = "enable" if enabled else "disable"
            self.cli.print_error(f"Usage: /cron {action} <job-id>")
            self.cli.print_info("Use /cron list to see job IDs")
            return

        job_id = args[0]
        success = self.cron_service.enable_job(job_id, enabled)

        if success:
            action = "enabled" if enabled else "disabled"
            self.cli.print_success(f"✓ Job {job_id} {action}")
        else:
            self.cli.print_error(f"Job {job_id} not found")
            self.cli.print_info("Use /cron list to see available jobs")

    async def _cron_remove_command(self, args: list):
        """Remove a cron job."""
        if len(args) < 1:
            self.cli.print_error("Usage: /cron remove <job-id>")
            self.cli.print_info("Use /cron list to see job IDs")
            return

        job_id = args[0]
        success = self.cron_service.remove_job(job_id)

        if success:
            self.cli.print_success(f"✓ Job {job_id} removed")
        else:
            self.cli.print_error(f"Job {job_id} not found")
            self.cli.print_info("Use /cron list to see available jobs")

    async def _cron_run_command(self, args: list):
        """Manually run a cron job now."""
        if len(args) < 1:
            self.cli.print_error("Usage: /cron run <job-id>")
            self.cli.print_info("Use /cron list to see job IDs")
            return

        job_id = args[0]
        success = await self.cron_service.run_job_now(job_id)

        if success:
            self.cli.print_success(f"✓ Job {job_id} triggered")
        else:
            self.cli.print_error(f"Job {job_id} not found")
            self.cli.print_info("Use /cron list to see available jobs")

    # =========================================================================
    # USER REQUEST PROCESSING
    # =========================================================================

    async def _run_team_stream(self, task: str):
        """
        Helper method to run team stream (can be cancelled)

        Args:
            task: The task/query for the team

        Returns:
            AsyncIterator of messages from the team
        """
        return self.main_team.run_stream(task=task)

    def _handle_interrupt(self, signum, frame):
        """
        Handle Ctrl+C interrupts (SIGINT)

        First interrupt: Cancel current agent task
        Second interrupt: Exit DaveAgent completely
        """
        self.interrupt_count += 1

        if self.interrupt_count == 1:
            # First Ctrl+C: Try to cancel current task
            if self.current_task and not self.current_task.done():
                self.logger.info("⚠️  First interrupt: Cancelling current agent task...")
                print("\n⚠️  Stopping agent task... (Press Ctrl+C again to exit completely)")
                self.current_task.cancel()
            else:
                # No task running, treat as exit
                print("\n⚠️  Exiting DaveAgent...")
                self.should_exit = True
        else:
            # Second Ctrl+C: Force exit
            self.logger.info("⚠️  Second interrupt: Forcing exit...")
            print("\n⚠️  Forcing exit...")
            self.should_exit = True

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
        - Planner: Complex multi-step tasks (planning and coordination)
        - Coder: All code operations (search, analysis, and modifications)
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
                max_results=3,  # Maximum skills to activate
                min_score=0.6,  # Minimum semantic similarity (0.0-1.0)
                # 0.6 = moderately relevant (strict enough to avoid false positives)
                # Lower = more permissive, higher = stricter matching
            )
            skills_context = ""

            if relevant_skills:
                skills_list = "\n".join([s.to_context_string() for s in relevant_skills])
                skills_context = f"\n\n<active_skills>\nThe following skills are relevant to your request and available for use:\n\n{skills_list}\n</active_skills>"
                self.logger.info(
                    f"🧠 RAG activated {len(relevant_skills)} relevant skill(s): {[s.name for s in relevant_skills]}"
                )
            else:
                self.logger.debug("🧠 No skills met the relevance threshold for this request")

            # Prepare final input with context
            # Combine: User Request + Mentioned Files + Skills Context
            full_input = f"{user_input}\n{mentioned_files_content}{skills_context}"

            self.logger.debug(f"Input context prepared with {len(skills_context)} chars of skills")
            self.logger.debug(f"📨 User request length: {len(full_input)} chars")

            # =================================================================
            # LET SELECTOR GROUP CHAT HANDLE EVERYTHING
            # =================================================================
            # No manual complexity detection - the SelectorGroupChat's model-based
            # selector intelligently routes to the appropriate agent based on:
            # - Agent descriptions (name + description attributes)
            # - Conversation context and history
            # - The nature of the user's request
            #
            # This is more efficient and intelligent than manual classification.
            # =================================================================

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
            # _run_team_stream is async and returns an async generator
            # We need to await it first to get the generator
            stream_generator = await self._run_team_stream(full_input)

            # Silence autogen internal loggers to avoid leaking raw tracebacks.
            self.logger.debug("🚀 Stream task started")

            # Track last message time to detect stuck state
            last_message_time = asyncio.get_event_loop().time()
            message_timeout = 600  # 10 minutes without messages = might be stuck (long tasks need time)

            # Log progress every N tool calls
            last_progress_log = 0
            progress_log_interval = 10  # Log every 10 tool calls

            try:
                # CRITICAL FIX: Iterate over async generator for true streaming
                # The await above gets the generator, now we iterate over it
                async for msg in stream_generator:
                    # Update last message time
                    last_message_time = asyncio.get_event_loop().time()
                    message_count += 1
                    msg_type = type(msg).__name__
                    msg_source = getattr(msg, "source", "unknown")

                    # DIAGNOSTIC: Log ALL message types with full details
                    content_preview = ""
                    if hasattr(msg, "content"):
                        c = msg.content
                        if isinstance(c, str):
                            content_preview = c[:80]
                        elif isinstance(c, list):
                            content_preview = f"[list with {len(c)} items]"
                        else:
                            content_preview = str(c)[:80]

                    self.logger.debug(
                        f"📨 Msg #{message_count} | Type: {msg_type:30} | Source: '{msg_source:10}' | "
                        f"Preview: {content_preview}"
                    )

                    # LOG FULL MESSAGE CONTENT for important types (helps debug missing messages)
                    if msg_type in ["TextMessage", "ThoughtEvent"]:
                        full_content = ""
                        if hasattr(msg, "content"):
                            full_content = str(msg.content)
                        self.logger.info(
                            f"📬 FULL MESSAGE RECEIVED:\n"
                            f"   Type: {msg_type}\n"
                            f"   Source: {msg_source}\n"
                            f"   Content:\n{full_content}\n"
                            f"   {'='*80}"
                        )

                    # Only process messages that are NOT from the user
                    # UPDATED: Also process messages without source (fallback)
                    should_process = False
                    if hasattr(msg, "source"):
                        if msg.source != "user":
                            should_process = True
                        else:
                            # DIAGNOSTIC: Check if this is actually an agent response incorrectly marked
                            if msg_type == "TextMessage" and hasattr(msg, "content"):
                                content = str(msg.content)
                                # Agent responses typically don't start with user-like phrases
                                if any(marker in content for marker in ["I'll", "I will", "I've", "Let me", "I have", "Based on", "TERMINATE"]):
                                    self.logger.warning(
                                        f"⚠️ TextMessage with source='user' but appears to be agent response! "
                                        f"Content: {content[:100]}"
                                    )

                    if should_process:
                        agent_name = msg.source

                        # Track which agents were used
                        if agent_name not in agents_used:
                            agents_used.append(agent_name)
                    else:
                        # Log why message was NOT processed
                        skip_reason = "unknown"
                        if hasattr(msg, "source"):
                            if msg.source == "user":
                                skip_reason = "source is 'user'"
                        else:
                            skip_reason = "no source attribute"
                        self.logger.debug(
                            f"⏭️  Skipping message: {msg_type} ({skip_reason})"
                        )

                    if should_process:

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
                            self.logger.debug(f"✅ Processing message (will show in terminal): {msg_type} from {agent_name}")

                            # SHOW DIFFERENT MESSAGE TYPES IN CONSOLE IN REAL-TIME
                        else:
                            self.logger.debug(f"⏭️  Skipping duplicate message: {msg_type} from {agent_name} (already shown)")

                        if message_key not in agent_messages_shown:
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

                            elif msg_type in ["ModelClientStreamingChunkEvent", "CodeGenerationEvent"]:
                                # Show streaming chunks and code generation events (agent thinking)
                                if spinner_active:
                                    self.cli.stop_thinking(clear=True)
                                    spinner_active = False
                                self.cli.print_thinking(f"🤔 {agent_name} is thinking...")
                                self.logger.debug(f"🧠 {msg_type}: {content_str[:200]}")
                                agent_messages_shown.add(message_key)

                            elif msg_type == "ToolCallRequestEvent":
                                # 🔧 Show tools to be called
                                # Stop spinner to show tool call, then restart with specific message
                                if spinner_active:
                                    self.cli.stop_thinking(clear=True)

                                # Log progress every N tool calls
                                if len(tools_called) - last_progress_log >= progress_log_interval:
                                    self.logger.info(
                                        f"📊 Progress: {len(tools_called)} tool calls completed, "
                                        f"{message_count} messages processed"
                                    )
                                    last_progress_log = len(tools_called)

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
                                            if (
                                                tool_name == "write_file"
                                                and isinstance(tool_args, dict)
                                                and "file_content" in tool_args
                                            ):
                                                # Show write_file with syntax highlighting
                                                target_file = tool_args.get("target_file", "unknown")
                                                file_content = tool_args.get("file_content", "")
                                                self.cli.print_thinking(
                                                    f"🔧 {agent_name} > {tool_name}: Writing to {target_file}"
                                                )
                                                await self.cli.print_code(
                                                    file_content, target_file, max_lines=50
                                                )
                                            elif tool_name == "edit_file" and isinstance(
                                                tool_args, dict
                                            ):
                                                # Show edit_file with unified diff
                                                import difflib

                                                target_file = tool_args.get("target_file", "unknown")
                                                old_string = tool_args.get("old_string", "")
                                                new_string = tool_args.get("new_string", "")
                                                instructions = tool_args.get("instructions", "")
                                                self.cli.print_thinking(
                                                    f"🔧 {agent_name} > {tool_name}: Editing {target_file}"
                                                )
                                                if instructions:
                                                    self.cli.print_thinking(f"   📝 {instructions}")
                                                # Generate unified diff
                                                old_lines = old_string.splitlines(keepends=True)
                                                new_lines = new_string.splitlines(keepends=True)
                                                diff = difflib.unified_diff(
                                                    old_lines,
                                                    new_lines,
                                                    fromfile=f"a/{target_file}",
                                                    tofile=f"b/{target_file}",
                                                    lineterm="",
                                                )
                                                diff_text = "".join(diff)
                                                if diff_text:
                                                    self.cli.print_diff(diff_text)
                                                else:
                                                    self.cli.print_thinking(
                                                        "   (no changes detected in diff)"
                                                    )
                                            else:
                                                # Default: show explanation (if provided) + parameters
                                                explanation = None
                                                if isinstance(tool_args, dict):
                                                    explanation = tool_args.get("explanation")

                                                # Show explanation prominently if available
                                                if explanation:
                                                    # Parse tool name to make it more readable
                                                    tool_display = tool_name.replace("_", " ").title()
                                                    self.cli.print_info(
                                                        f"🔧 {tool_display}: {explanation}",
                                                        agent_name,
                                                    )
                                                    # Show compact parameters (without explanation)
                                                    params_copy = {k: v for k, v in tool_args.items() if k != "explanation"}
                                                    if params_copy:
                                                        params_str = str(params_copy)
                                                        if len(params_str) > 150:
                                                            params_str = params_str[:150] + "..."
                                                        self.cli.print_thinking(f"   Parameters: {params_str}")
                                                else:
                                                    # No explanation - show old format
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
                                        self.logger.debug(
                                            f"🚀 STARTING EXECUTION of {len(tool_names)} tool(s): {', '.join(tool_names)}"
                                        )
                                        self.logger.debug(f"executing {tool_names[0]}")
                                        # Start spinner with context about what's executing
                                        tool_desc = tool_names[0].replace("_", " ")
                                        self.cli.start_thinking(message=f"executing {tool_desc}")
                                        spinner_active = True
                                agent_messages_shown.add(message_key)

                            elif msg_type == "ToolCallExecutionEvent":
                                # ✅ Show tool results
                                self.logger.debug(f"🎯 ToolCallExecutionEvent RECEIVED (results ready)")

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
                                            self.logger.debug(
                                                f"🔧 Tool '{tool_name}' execution completed, "
                                                f"result length: {len(result_content)} chars"
                                            )

                                            # 🚨 CRITICAL: Detect user cancellation in tool results
                                            # When a tool is cancelled, ask_for_approval raises UserCancelledError,
                                            # but AutoGen converts it to a string result. We need to detect this
                                            # and re-raise the exception to stop the entire workflow.
                                            if (
                                                "User selected 'No, cancel'" in result_content
                                                or "UserCancelledError" in result_content
                                            ):
                                                self.logger.info(
                                                    "🚫 User cancelled tool execution - stopping workflow"
                                                )
                                                raise UserCancelledError(
                                                    "User cancelled tool execution"
                                                )

                                            # DEBUG: Log tool result details
                                            self.logger.debug(
                                                f"[TOOL_RESULT_DEBUG] tool_name={tool_name}, result_starts_with={result_content[:50] if len(result_content) > 50 else result_content}, has_File={('File:' in result_content)}"
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
                                                        filename = first_line.replace(
                                                            "File:", ""
                                                        ).strip()
                                                        # Get code content (everything after first line)
                                                        code_content = "\n".join(
                                                            result_content.split("\n")[1:]
                                                        )
                                                        # Display with syntax highlighting (async to prevent blocking)
                                                        await self.cli.print_code(
                                                            code_content, filename, max_lines=50
                                                        )
                                                        self.logger.debug(
                                                            f"✅ Tool result: {tool_name} -> {filename} (displayed with syntax highlighting)"
                                                        )
                                                    else:
                                                        # Fallback
                                                        result_preview = result_content[:100]
                                                        self.cli.print_thinking(
                                                            f"✅ {agent_name} > {tool_name}: {result_preview}..."
                                                        )
                                                except Exception:
                                                    result_preview = result_content[:100]
                                                    self.cli.print_thinking(
                                                        f"✅ {agent_name} > {tool_name}: {result_preview}..."
                                                    )
                                            elif (
                                                tool_name == "write_file"
                                                and "Successfully wrote" in result_content
                                            ):
                                                # Special handling for write_file - show success message
                                                self.cli.print_success(
                                                    f"{agent_name} > {tool_name}: {result_content}"
                                                )
                                                self.logger.debug(
                                                    f"✅ Tool result: {tool_name} -> {result_content}"
                                                )
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

                                # Restart spinner for next action with better context
                                self.cli.start_thinking(message=f"{agent_name} analyzing results")
                                spinner_active = True
                                agent_messages_shown.add(message_key)

                                # 💾 AUTO-SAVE after each tool execution (non-blocking)
                                asyncio.create_task(self._auto_save_agent_states())

                            elif msg_type == "TextMessage":
                                # 💬 TextMessage can be:
                                # 1. Agent reasoning/reflection BEFORE tool call (when reflect_on_tool_use=True)
                                # 2. Final agent response
                                # We need to distinguish between them

                                # Check if this looks like reasoning (typically shorter, discusses what to do)
                                is_reasoning = False
                                reasoning_indicators = [
                                    "let me", "i'll", "i will", "first", "now", "next",
                                    "to do this", "i need to", "i should", "let's",
                                    "i can", "i must", "going to"
                                ]
                                content_lower = content_str.lower()
                                if any(indicator in content_lower for indicator in reasoning_indicators):
                                    # Short messages are likely reasoning
                                    if len(content_str) < 500:
                                        is_reasoning = True

                                if is_reasoning:
                                    # Show as thinking/reasoning (different style)
                                    if spinner_active:
                                        self.cli.stop_thinking(clear=True)
                                        spinner_active = False
                                    self.logger.debug(f"🖥️  SHOWING IN TERMINAL (reasoning): {content_str[:100]}")
                                    self.cli.print_thinking(f"💭 {agent_name} is thinking: {content_str}")
                                    self.logger.debug(f"💭 Reasoning: {content_str}")
                                    self.json_logger.log_thought(agent_name, content_str)
                                    agent_messages_shown.add(message_key)
                                    # Don't restart spinner - let next event handle it
                                else:
                                    # Show as final agent response
                                    if spinner_active:
                                        self.cli.stop_thinking(clear=True)
                                        spinner_active = False

                                    preview = content_str[:100] if len(content_str) > 100 else content_str
                                    self.logger.log_message_processing(msg_type, agent_name, preview)
                                    self.logger.debug(f"🖥️  SHOWING IN TERMINAL (final response): {content_str[:200]}")
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

                                # 💾 AUTO-SAVE after each agent TextMessage (non-blocking)
                                asyncio.create_task(self._auto_save_agent_states())

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

                # ============= END JSON LOGGING SESSION =============
                # Save all captured events to timestamped JSON file
                self.json_logger.end_session(summary="Request completed successfully")

            finally:
                self.logger.debug("🏁 Stream finished (finally block)")
                # Always reset current task when stream finishes
                self.current_task = None
                # 💾 AUTO-SAVE: Always save state after each request, even on error
                await self._auto_save_agent_states()

        except asyncio.CancelledError:
            # Stop spinner on cancellation
            self.cli.stop_thinking()

            # Show cancellation message
            self.cli.print_warning("\n\n⚠️  Agent task stopped (Ctrl+C)")
            self.cli.print_info("ℹ️  Press Ctrl+C again to exit DaveAgent completely.")
            self.logger.info("Agent task cancelled by user interrupt")

            # End JSON logging session
            self.json_logger.end_session(summary="Task cancelled by interrupt")

            # Reset current task and save state
            self.current_task = None
            await self._auto_save_agent_states()

        except UserCancelledError:
            # Stop spinner on user cancellation
            if spinner_active:
                self.cli.stop_thinking()

            # Clear message and show cancellation
            self.cli.print_error("\n\n🚫 Task cancelled by user.")
            self.cli.print_info("ℹ️  You can start a new task whenever you're ready.")
            self.logger.info("Task explicitly cancelled by user during tool approval.")

            # End JSON logging session
            self.json_logger.end_session(summary="Task cancelled by user")
            await self._auto_save_agent_states()

        except Exception as e:
            # Stop spinner on error
            self.cli.stop_thinking()

            error_str = str(e)

            # Handle token limit errors (BadRequestError 400) - should be rare with compression
            is_token_limit_error = (
                "maximum context length" in error_str.lower()
                or "requested" in error_str and "tokens" in error_str
                or "BadRequestError" in type(e).__name__ and "400" in error_str
            )

            if is_token_limit_error:
                self.logger.error(
                    "🚨 Token limit exceeded! This should have been prevented by compression. "
                    "Forcing emergency context cleanup..."
                )

                self.cli.print_error(
                    "⚠️ Context exceeded maximum tokens. The compression system should have "
                    "prevented this, but we'll perform emergency cleanup."
                )

                # Emergency fallback: Reset agent contexts to smaller buffer
                try:
                    from autogen_core.model_context import BufferedChatCompletionContext

                    # Reduce buffer size dramatically for emergency recovery
                    self.coder_agent._model_context = BufferedChatCompletionContext(buffer_size=30)
                    self.planning_agent._model_context = BufferedChatCompletionContext(buffer_size=30)

                    self.cli.print_warning(
                        "⚠️ Agent contexts have been reset to keep only recent messages. "
                        "Some conversation history was lost."
                    )

                    self.cli.print_info(
                        "💡 To prevent this, consider starting a new session with /new-session "
                        "or saving current progress with /save-state"
                    )

                    self.logger.info("Emergency context reset complete: buffer_size=30")

                except Exception as reset_error:
                    self.logger.error(f"Failed to reset contexts: {reset_error}")
                    self.cli.print_error(
                        "Failed to recover from token limit error. Please start a new session with /new-session"
                    )

                # Still log the error but don't continue with normal error handling
                self.json_logger.log_error(e, context="token_limit_exceeded")
                await self._auto_save_agent_states()
                return

            # Handle authentication errors (401) by prompting reconfiguration
            is_auth_error = (
                "401" in error_str
                or "authentication" in error_str.lower()
                or "AuthenticationError" in type(e).__name__
                or "invalid_api_key" in error_str.lower()
                or "Authentication Fails" in error_str
            )
            if is_auth_error:
                self.cli.print_error(
                    "❌ Authentication failed: your API key is invalid or missing."
                )
                self.cli.print_info(
                    "🔧 Let's reconfigure your provider and API key."
                )
                try:
                    await self._reconfigure_from_setup_wizard()
                    self.cli.print_success(
                        "✅ Configuration updated. Please retry your request."
                    )
                except Exception as setup_err:
                    self.logger.error(f"Reconfiguration failed: {setup_err}")
                    self.cli.print_error(
                        f"Failed to reconfigure: {setup_err}"
                    )
                return

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

            # Save state even on error
            await self._auto_save_agent_states()

            # AUTOMATIC ERROR REPORTING TO SIGNOZ
            self.cli.print_thinking("📊 Reporting error to SigNoz...")
            try:
                await self.error_reporter.report_error(
                    exception=e, context="process_user_request", severity="error"
                )
            except Exception as report_err:
                self.logger.error(f"Failed to report error: {report_err}")

    # =========================================================================
    # AUTHENTICATION RECONFIGURATION
    # =========================================================================

    async def _reconfigure_from_setup_wizard(self):
        """
        Runs the interactive setup wizard and updates all model clients
        with the new API key, base URL and model.
        """
        import asyncio
        from src.utils.setup_wizard import run_interactive_setup
        import httpx

        # Run setup wizard in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        api_key, base_url, model = await loop.run_in_executor(
            None, run_interactive_setup
        )

        # Update settings
        self.settings.api_key = api_key
        if base_url:
            self.settings.base_url = base_url
        if model:
            self.settings.model = model
            self.settings.base_model = model
            self.settings.strong_model = model

        # Rebuild HTTP client
        http_client = httpx.AsyncClient(verify=self.settings.ssl_verify)

        # Rebuild model clients with new credentials
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        self.client_base = OpenAIChatCompletionClient(
            model=self.settings.base_model,
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            model_info=self.settings.get_model_capabilities(),
            custom_http_client=http_client,
        )

        is_deepseek_reasoner = (
            "deepseek-reasoner" in self.settings.strong_model.lower()
            and "deepseek" in self.settings.base_url.lower()
        )
        if is_deepseek_reasoner:
            from src.utils.deepseek_reasoning_client import DeepSeekReasoningClient

            self.client_strong = DeepSeekReasoningClient(
                model=self.settings.strong_model,
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                model_info=self.settings.get_model_capabilities(),
                custom_http_client=http_client,
                enable_thinking=None,
            )
        else:
            self.client_strong = OpenAIChatCompletionClient(
                model=self.settings.strong_model,
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                model_info=self.settings.get_model_capabilities(),
                custom_http_client=http_client,
            )

        # Update the wrapped model_client reference
        if hasattr(self.model_client, "_wrapped"):
            self.model_client._wrapped = self.client_strong

        self.logger.info(
            f"Reconfigured: provider={self.settings.base_url}, model={self.settings.strong_model}"
        )

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
                except Exception:
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
                    # Load team state
                    team_loaded = await self.state_manager.load_team_state(self.main_team, self.client_strong)

                    # Get metadata
                    metadata = self.state_manager.get_session_metadata()
                    messages = self.state_manager.get_session_history()

                    # Display success
                    self.cli.print_success(f"\n✅ Session loaded: {title}")
                    self.cli.print_info(f"  • Team state restored: {team_loaded}")
                    self.cli.print_info(f"  • Agents restored: {1 if team_loaded else 0}")

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
        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._handle_interrupt)

        self.cli.print_banner()

        # Start cron service
        await self.cron_service.start()
        self.logger.info("⏰ Cron service started")

        # Start system message detector (FASE 3: Auto-Injection)
        await self.start_system_message_detector()

        # Check for previous sessions and offer to resume
        await self._check_and_resume_session()

        try:
            while self.running:
                # Check if should exit (from Ctrl+C handler)
                if self.should_exit:
                    self.logger.info("⚠️  Exiting due to user interrupt")
                    break

                # Reset interrupt counter when waiting for new input
                self.interrupt_count = 0

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
            # This should not happen often with signal handler
            self.logger.warning("⚠️ Keyboard interrupt (Ctrl+C) - caught in exception handler")
            self.cli.print_warning("\n\n⚠️  Exiting DaveAgent...")

        except Exception as e:
            self.logger.log_error_with_context(e, "main loop")
            self.cli.print_error(f"Fatal error: {str(e)}")

            # AUTOMATIC ERROR REPORTING FOR FATAL ERRORS
            try:
                await self.error_reporter.report_error(
                    exception=e, context="main_loop_fatal_error", severity="critical"
                )
            except Exception as report_err:
                self.logger.error(f"Failed to report fatal error: {report_err}")

        finally:
            self.logger.info("🔚 Closing DaveAgent CLI")
            self.cli.print_goodbye()

            # Stop system message detector (FASE 3: Auto-Injection)
            try:
                await self.stop_system_message_detector()
            except Exception as e:
                self.logger.error(f"Error stopping system message detector: {e}")

            # Stop cron service
            try:
                await self.cron_service.stop()
                self.logger.info("⏰ Cron service stopped")
            except Exception as e:
                self.logger.error(f"Error stopping cron service: {e}")

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
    )
    await app.run()


if __name__ == "__main__":
    import sys

    # Detect if --debug flag was passed
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    if debug_mode:
        print("🐛 DEBUG mode enabled")

    asyncio.run(main(debug=debug_mode))
