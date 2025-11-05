"""
Archivo principal - Interfaz CLI completa del agente de código
NUEVA ESTRUCTURA REORGANIZADA (CORREGIDA CON LOGGING)
"""
import asyncio
import logging
from autogen_agentchat.agents import AssistantAgent
# Importaciones añadidas para el nuevo flujo
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Importar desde nueva estructura
from src.config import (
    CODER_AGENT_DESCRIPTION,
    COMPLEXITY_DETECTOR_PROMPT,
    PLANNING_AGENT_DESCRIPTION,
    PLANNING_AGENT_SYSTEM_MESSAGE,
    SUMMARY_AGENT_DESCRIPTION,
    SUMMARY_AGENT_SYSTEM_MESSAGE
)
from src.agents import CodeSearcher
from src.config.prompts import AGENT_SYSTEM_PROMPT
from src.managers import StateManager
from src.interfaces import CLIInterface
from src.utils import get_logger, get_conversation_tracker, HistoryViewer
from src.memory import MemoryManager, DocumentIndexer


class DaveAgentCLI:
    """Aplicación CLI principal del agente de código"""

    def __init__(
        self,
        debug: bool = False,
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ):
        """
        Inicializa todos los componentes del agente

        Args:
            debug: Modo debug activado
            api_key: API key para el modelo LLM
            base_url: URL base de la API
            model: Nombre del modelo a usar
        """
        # Configurar logging (ahora en .daveagent/logs/)
        log_level = logging.DEBUG if debug else logging.INFO
        self.logger = get_logger(log_file=None, level=log_level)  # Use default path

        # Configurar conversation tracker (logs to .daveagent/conversations.json)
        self.conversation_tracker = get_conversation_tracker()

        self.logger.info("🚀 Inicializando DaveAgent CLI")

        # Cargar configuración (API key, URL, modelo)
        from src.config import get_settings

        self.settings = get_settings(api_key=api_key, base_url=base_url, model=model)

        # Validar configuración
        is_valid, error_msg = self.settings.validate()
        if not is_valid:
            self.logger.error(f"❌ Configuración inválida: {error_msg}")
            print(error_msg)
            raise ValueError("Configuración inválida")

        self.logger.info(f"✓ Configuración cargada: {self.settings}")

        # Crear cliente del modelo
        self.logger.debug(f"Configurando cliente del modelo: {self.settings.model}")
        self.model_client = OpenAIChatCompletionClient(
            model=self.settings.model,
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            model_capabilities=self.settings.get_model_capabilities(),
        )

        # Sistema de memoria con ChromaDB (inicializar ANTES de crear agentes)
        self.logger.info("🧠 Inicializando sistema de memoria...")
        self.memory_manager = MemoryManager(
            k=5,  # Top 5 resultados más relevantes
            score_threshold=0.3  # Umbral de similitud
        )

        # Sistema de gestión de estado (AutoGen save_state/load_state)
        self.logger.info("💾 Inicializando sistema de estado...")
        self.state_manager = StateManager(
            auto_save_enabled=True,
            auto_save_interval=300  # Auto-save cada 5 minutos
        )

        # Importar todas las herramientas desde la nueva estructura
        from src.tools import (
            # Filesystem
            read_file, write_file, list_dir, edit_file,
            delete_file, file_search, reapply,
            # Git
            git_status, git_add, git_commit, git_push, git_pull,
            git_log, git_branch, git_diff,
            # JSON
            read_json, write_json, merge_json_files, validate_json,
            format_json, json_get_value, json_set_value, json_to_text,
            # CSV
            read_csv, write_csv, csv_info, filter_csv,
            merge_csv, csv_to_json, sort_csv,
            # Web
            wiki_search, wiki_summary, wiki_content,
            wiki_page_info, wiki_random, wiki_set_language,
            web_search, web_search_news,
            # Analysis
            analyze_python_file, find_function_definition, list_all_functions,
            codebase_search, grep_search, run_terminal_cmd, diff_history,
            # Validation
            validate_python_syntax, validate_javascript_syntax,
            validate_typescript_syntax, validate_json_file,
            validate_file_after_edit, validate_generic_file
        )

        coder_tools = [
            # Filesystem (7 tools)
            read_file, write_file, list_dir, edit_file, delete_file, file_search, reapply,
            # Git (8 tools)
            git_status, git_add, git_commit, git_push, git_pull, git_log, git_branch, git_diff,
            # JSON (8 tools)
            read_json, write_json, merge_json_files, validate_json,
            format_json, json_get_value, json_set_value, json_to_text,
            # CSV (7 tools)
            read_csv, write_csv, csv_info, filter_csv, merge_csv, csv_to_json, sort_csv,
            # Web (8 tools)
            wiki_search, wiki_summary, wiki_content, wiki_page_info, wiki_random, wiki_set_language,
            web_search, web_search_news,
            # Analysis (7 tools)
            analyze_python_file, find_function_definition, list_all_functions,
            codebase_search, grep_search, run_terminal_cmd, diff_history,
            # Validation (6 tools)
            validate_python_syntax, validate_javascript_syntax, validate_typescript_syntax,
            validate_json_file, validate_file_after_edit, validate_generic_file
        ]

        # Crear agente de código con memoria de conversaciones y código base
        self.coder_agent = AssistantAgent(
            name="Coder",
            description=CODER_AGENT_DESCRIPTION,
            system_message=AGENT_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=coder_tools,
            max_tool_iterations=5,
            reflect_on_tool_use=False,
            memory=[
                self.memory_manager.conversation_memory,  # Conversaciones previas
                self.memory_manager.codebase_memory,  # Código base indexado
                self.memory_manager.preferences_memory  # Preferencias del usuario
            ]
        )

        # Componentes del sistema
        self.cli = CLIInterface()
        self.history_viewer = HistoryViewer(console=self.cli.console)

        # Crear CodeSearcher con las herramientas de análisis y memoria de código
        search_tools = [
            # Herramientas de búsqueda
            codebase_search, grep_search, file_search,
            # Herramientas de lectura
            read_file, list_dir,
            # Herramientas de análisis Python
            analyze_python_file, find_function_definition, list_all_functions,
        ]
        self.code_searcher = CodeSearcher(
            self.model_client,
            search_tools,
            memory=[self.memory_manager.codebase_memory]  # Memoria de código indexado
        )

        # ============= NUEVOS AGENTES PARA ARQUITECTURA OPTIMIZADA =============

        # PlanningAgent: Crea y gestiona planes para tareas complejas
        # Con memoria de decisiones previas y planes exitosos
        self.planning_agent = AssistantAgent(
            name="Planner",
            description=PLANNING_AGENT_DESCRIPTION,
            system_message=PLANNING_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=[],  # No necesita herramientas, solo planifica
            memory=[self.memory_manager.decision_memory]  # Memoria de decisiones
        )

        # SummaryAgent: Crea resúmenes finales de trabajo completado
        self.summary_agent = AssistantAgent(
            name="SummaryAgent",
            description=SUMMARY_AGENT_DESCRIPTION,
            system_message=SUMMARY_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=[],  # No necesita herramientas, solo resume
        )

        self.running = True

    async def handle_command(self, command: str) -> bool:
        """Maneja comandos especiales del usuario"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd in ["/exit", "/quit"]:
            return False

        elif cmd == "/help":
            self.cli.print_help()

        elif cmd == "/clear":
            # Clear screen only - AutoGen handles history
            self.cli.clear_screen()
            self.cli.print_success("Pantalla limpiada")

        elif cmd == "/new":
            # Just clear screen - new session will be auto-created if needed
            self.cli.clear_screen()
            self.cli.print_success("Nueva conversación iniciada")

        elif cmd == "/new-session":
            # Crear nueva sesión con metadata
            await self._new_session_command(parts)

        elif cmd == "/save-state" or cmd == "/save-session":
            # Guardar estado completo usando AutoGen save_state
            await self._save_state_command(parts)

        elif cmd == "/load-state" or cmd == "/load-session":
            # Cargar estado usando AutoGen load_state
            await self._load_state_command(parts)

        elif cmd == "/list-sessions" or cmd == "/sessions":
            # Listar sesiones guardadas con tabla Rich
            await self._list_sessions_command()

        elif cmd == "/history":
            # Mostrar historial de la sesión actual
            await self._show_history_command(parts)

        # REMOVED: /load command - Use /load-state instead (AutoGen official)

        elif cmd == "/debug":
            # Cambiar nivel de logging
            current_level = self.logger.logger.level
            if current_level == logging.DEBUG:
                self.logger.logger.setLevel(logging.INFO)
                self.cli.print_success("🔧 Modo debug DESACTIVADO (nivel: INFO)")
                self.logger.info("Nivel de logging cambiado a INFO")
            else:
                self.logger.logger.setLevel(logging.DEBUG)
                self.cli.print_success("🐛 Modo debug ACTIVADO (nivel: DEBUG)")
                self.logger.debug("Nivel de logging cambiado a DEBUG")

        elif cmd == "/logs":
            # Mostrar ubicación del archivo de logs
            log_files = list(self.logger.logger.handlers)
            file_handlers = [h for h in log_files if isinstance(h, logging.FileHandler)]
            if file_handlers:
                log_path = file_handlers[0].baseFilename
                self.cli.print_info(f"📄 Archivo de logs: {log_path}")
            else:
                self.cli.print_info("No hay archivos de log configurados")

        elif cmd == "/search":
            # Invocar CodeSearcher para buscar en el código
            if len(parts) < 2:
                self.cli.print_error("Uso: /search <consulta>")
                self.cli.print_info("Ejemplo: /search función de autenticación")
            else:
                query = parts[1]
                self.cli.print_thinking(f"🔍 Buscando en el código: {query}")
                await self._run_code_searcher(query)

        elif cmd == "/index":
            # Indexar el proyecto en memoria
            self.cli.print_info("📚 Indexando proyecto en memoria vectorial...")
            await self._index_project()

        elif cmd == "/memory":
            # Mostrar estadísticas de memoria
            if len(parts) < 2:
                await self._show_memory_stats()
            else:
                subcommand = parts[1].lower()
                if subcommand == "clear":
                    await self._clear_memory()
                elif subcommand == "query":
                    self.cli.print_info("Uso: /memory query <texto>")
                else:
                    self.cli.print_error(f"Subcomando desconocido: {subcommand}")
                    self.cli.print_info("Uso: /memory [clear|query]")

        else:
            self.cli.print_error(f"Comando desconocido: {cmd}")
            self.cli.print_info("Usa /help para ver los comandos disponibles")

        return True

    # =========================================================================
    # MEMORY MANAGEMENT - Gestión de memoria vectorial
    # =========================================================================

    async def _index_project(self):
        """Indexa el proyecto actual en memoria vectorial"""
        try:
            from pathlib import Path

            self.cli.start_thinking()
            self.logger.info("📚 Iniciando indexación del proyecto...")

            # Crear indexer
            indexer = DocumentIndexer(
                memory=self.memory_manager.codebase_memory,
                chunk_size=1500
            )

            # Indexar directorio actual
            project_dir = Path.cwd()
            stats = await indexer.index_project(
                project_dir=project_dir,
                max_files=500  # Limitar a 500 archivos para no sobrecargar
            )

            self.cli.stop_thinking()

            # Mostrar estadísticas
            self.cli.print_success(f"✅ Indexación completada!")
            self.cli.print_info(f"  • Archivos indexados: {stats['files_indexed']}")
            self.cli.print_info(f"  • Chunks creados: {stats['chunks_created']}")
            self.cli.print_info(f"  • Archivos omitidos: {stats['files_skipped']}")
            if stats['errors'] > 0:
                self.cli.print_warning(f"  • Errores: {stats['errors']}")

            self.logger.info(f"✅ Proyecto indexado: {stats}")

        except Exception as e:
            self.cli.stop_thinking()
            self.logger.log_error_with_context(e, "_index_project")
            self.cli.print_error(f"Error indexando proyecto: {str(e)}")

    async def _show_memory_stats(self):
        """Muestra estadísticas de memoria"""
        try:
            self.cli.print_info("\n🧠 Estadísticas de Memoria Vectorial\n")

            # Nota: ChromaDB no expone fácilmente el conteo de items
            # Podríamos hacer queries dummy o mantener contadores
            # Por ahora, mostrar información general

            self.cli.print_info("📚 Sistema de memoria activo con 4 colecciones:")
            self.cli.print_info("  • Conversations: Historial de conversaciones")
            self.cli.print_info("  • Codebase: Código fuente indexado")
            self.cli.print_info("  • Decisions: Decisiones arquitectónicas")
            self.cli.print_info("  • Preferences: Preferencias del usuario")

            memory_path = self.memory_manager.persistence_path
            self.cli.print_info(f"\n💾 Ubicación: {memory_path}")

            # Calcular tamaño del directorio de memoria
            try:
                from pathlib import Path
                total_size = sum(f.stat().st_size for f in Path(memory_path).rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                self.cli.print_info(f"📊 Tamaño total: {size_mb:.2f} MB")
            except Exception as e:
                self.logger.warning(f"No se pudo calcular tamaño: {e}")

            self.cli.print_info("\n💡 Comandos disponibles:")
            self.cli.print_info("  • /index - Indexar proyecto actual")
            self.cli.print_info("  • /memory clear - Limpiar toda la memoria")

        except Exception as e:
            self.logger.log_error_with_context(e, "_show_memory_stats")
            self.cli.print_error(f"Error mostrando estadísticas: {str(e)}")

    async def _clear_memory(self):
        """Limpia toda la memoria vectorial"""
        try:
            self.cli.print_warning("⚠️  ¿Estás seguro de que quieres borrar TODA la memoria?")
            self.cli.print_info("Esto eliminará:")
            self.cli.print_info("  • Historial de conversaciones")
            self.cli.print_info("  • Código base indexado")
            self.cli.print_info("  • Decisiones arquitectónicas")
            self.cli.print_info("  • Preferencias del usuario")

            # En CLI no tenemos confirmación interactiva fácil
            # Por seguridad, requerir un segundo comando
            self.cli.print_warning("\n⚠️  Para confirmar, ejecuta: /memory clear confirm")

        except Exception as e:
            self.logger.log_error_with_context(e, "_clear_memory")
            self.cli.print_error(f"Error limpiando memoria: {str(e)}")

    # =========================================================================
    # STATE MANAGEMENT - Gestión de estado con AutoGen save_state/load_state
    # =========================================================================

    async def _new_session_command(self, parts: list):
        """
        Comando /new-session: Crea una nueva sesión con metadata

        Uso:
            /new-session <título>
            /new-session "Mi proyecto web" --tags backend,api --desc "API REST con FastAPI"
        """
        try:
            # Parse arguments
            import shlex
            
            if len(parts) < 2:
                self.cli.print_error("Uso: /new-session <título> [--tags tag1,tag2] [--desc descripción]")
                self.cli.print_info("Ejemplo: /new-session \"Proyecto Web\" --tags python,web --desc \"Desarrollo de API\"")
                return

            # Join and parse
            cmd_str = " ".join(parts[1:])
            
            # Extract title (first argument)
            args = shlex.split(cmd_str)
            if not args:
                self.cli.print_error("Debes proporcionar un título para la sesión")
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
                session_id=session_id,
                title=title,
                tags=tags,
                description=description
            )

            self.cli.print_success(f"✅ Nueva sesión creada: {title}")
            self.cli.print_info(f"  • Session ID: {session_id}")
            if tags:
                self.cli.print_info(f"  • Tags: {', '.join(tags)}")
            if description:
                self.cli.print_info(f"  • Descripción: {description}")

            self.logger.info(f"✅ Nueva sesión creada: {session_id} - {title}")

        except Exception as e:
            self.logger.log_error_with_context(e, "_new_session_command")
            self.cli.print_error(f"Error creando sesión: {str(e)}")

    async def _generate_session_title(self) -> str:
        """
        Genera un título descriptivo para la sesión usando LLM basado en el historial

        Returns:
            Título generado (máximo 50 caracteres)
        """
        try:
            # Obtener mensajes del historial actual
            messages = self.state_manager.get_session_history()
            
            if not messages or len(messages) < 2:
                return "Untitled Session"
            
            # Tomar los primeros mensajes para entender el contexto
            context_messages = messages[:5]  # Primeros 5 mensajes
            
            # Formatear contexto
            conversation_summary = ""
            for msg in context_messages:
                role = msg.get("source", "unknown")
                content = msg.get("content", "")
                # Limitar longitud de cada mensaje
                content_preview = content[:200] if len(content) > 200 else content
                conversation_summary += f"{role}: {content_preview}\n"
            
            # Crear prompt para generar título
            title_prompt = f"""Based on the following conversation, generate a short, descriptive title (maximum 50 characters).
The title should capture the main topic or task being discussed.

CONVERSATION:
{conversation_summary}

Generate ONLY the title text, nothing else. Make it concise and descriptive.
Examples: "Python API Development", "Bug Fix in Authentication", "Database Migration Setup"

TITLE:"""

            # Llamar al LLM
            from autogen_core.models import UserMessage
            result = await self.model_client.create(
                messages=[UserMessage(content=title_prompt, source="user")]
            )
            
            # Extraer título
            title = result.content.strip()
            
            # Limpiar título (remover comillas, etc.)
            title = title.strip('"').strip("'").strip()
            
            # Limitar longitud
            if len(title) > 50:
                title = title[:47] + "..."
            
            self.logger.info(f"📝 Título generado: {title}")
            return title
            
        except Exception as e:
            self.logger.warning(f"Error generando título: {e}")
            return "Untitled Session"

    async def _auto_save_agent_states(self):
        """
        Auto-guarda el estado de todos los agentes después de cada respuesta.
        Se ejecuta silenciosamente en background.
        Genera un título automático si la sesión no tiene uno.
        """
        try:
            # Iniciar sesión si no está iniciada
            if not self.state_manager.session_id:
                from datetime import datetime
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Generar título automáticamente usando LLM
                title = await self._generate_session_title()
                
                self.state_manager.start_session(
                    session_id=session_id,
                    title=title
                )
                self.logger.info(f"🎯 Nueva sesión creada con título: {title}")

            # Guardar estado de cada agente
            await self.state_manager.save_agent_state(
                "coder",
                self.coder_agent,
                metadata={"description": "Main coder agent with tools"}
            )

            await self.state_manager.save_agent_state(
                "code_searcher",
                self.code_searcher.searcher_agent,
                metadata={"description": "Code search and analysis agent"}
            )

            await self.state_manager.save_agent_state(
                "planning",
                self.planning_agent,
                metadata={"description": "Planning and task management agent"}
            )

            await self.state_manager.save_agent_state(
                "summary",
                self.summary_agent,
                metadata={"description": "Summary generation agent"}
            )

            # Guardar a disco
            await self.state_manager.save_to_disk()

            self.logger.debug("💾 Auto-save: Estado guardado automáticamente")

        except Exception as e:
            # No fallar si el auto-save falla, solo log
            self.logger.warning(f"⚠️ Auto-save falló: {str(e)}")

    async def _save_state_command(self, parts: list):
        """
        Comando /save-state o /save-session: Guarda el estado completo de agentes y teams

        Uso:
            /save-state                  # Guarda sesión actual
            /save-state <título>         # Guarda con título específico (crea nueva sesión)
            /save-session <título>       # Alias
        """
        try:
            self.cli.start_thinking(message="guardando sesión")
            self.logger.info("💾 Guardando estado de agentes...")

            # Determinar si es nueva sesión o actualización
            if len(parts) > 1 and not self.state_manager.session_id:
                # Nueva sesión con título manual
                title = " ".join(parts[1:])
                from datetime import datetime
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                self.state_manager.start_session(
                    session_id=session_id,
                    title=title
                )
            elif not self.state_manager.session_id:
                # Auto-generar sesión con título automático usando LLM
                from datetime import datetime
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Generar título inteligente
                title = await self._generate_session_title()
                
                self.state_manager.start_session(
                    session_id=session_id,
                    title=title
                )
                self.logger.info(f"📝 Título generado automáticamente: {title}")
            else:
                # Actualizar sesión existente
                session_id = self.state_manager.session_id

            # Guardar estado de cada agente
            await self.state_manager.save_agent_state(
                "coder",
                self.coder_agent,
                metadata={"description": "Main coder agent with tools"}
            )

            await self.state_manager.save_agent_state(
                "code_searcher",
                self.code_searcher.searcher_agent,
                metadata={"description": "Code search and analysis agent"}
            )

            await self.state_manager.save_agent_state(
                "planning",
                self.planning_agent,
                metadata={"description": "Planning and task management agent"}
            )

            await self.state_manager.save_agent_state(
                "summary",
                self.summary_agent,
                metadata={"description": "Summary generation agent"}
            )

            # Guardar a disco
            state_path = await self.state_manager.save_to_disk(session_id)

            self.cli.stop_thinking()

            # Get metadata and messages for display
            metadata = self.state_manager.get_session_metadata()
            messages = self.state_manager.get_session_history()

            self.cli.print_success(f"✅ Estado guardado correctamente!")
            self.cli.print_info(f"  • Título: {metadata.get('title', 'Sin título')}")
            self.cli.print_info(f"  • Session ID: {session_id}")
            self.cli.print_info(f"  • Ubicación: {state_path}")
            self.cli.print_info(f"  • Agentes guardados: 4")
            self.cli.print_info(f"  • Mensajes guardados: {len(messages)}")

            self.logger.info(f"✅ Estado guardado en sesión: {session_id}")

        except Exception as e:
            self.cli.stop_thinking()
            self.logger.log_error_with_context(e, "_save_state_command")
            self.cli.print_error(f"Error guardando estado: {str(e)}")

    async def _load_state_command(self, parts: list):
        """
        Comando /load-state o /load-session: Carga el estado de agentes desde una sesión
        y muestra el historial completo

        Uso:
            /load-state                  # Carga sesión más reciente
            /load-state my_session       # Carga sesión específica
            /load-session <session_id>   # Alias
        """
        try:
            self.cli.start_thinking(message="cargando sesión")
            self.logger.info("📂 Cargando estado de agentes...")

            # Determinar session_id
            if len(parts) > 1:
                session_id = parts[1]
            else:
                # Usar sesión más reciente
                sessions = self.state_manager.list_sessions()
                if not sessions:
                    self.cli.stop_thinking()
                    self.history_viewer.display_no_sessions()
                    return

                session_id = sessions[0]["session_id"]
                title = sessions[0].get("title", "Sesión más reciente")
                self.history_viewer.display_loading_session(session_id, title)

            # Cargar desde disco
            loaded = await self.state_manager.load_from_disk(session_id)

            if not loaded:
                self.cli.stop_thinking()
                self.cli.print_error(f"No se encontró sesión: {session_id}")
                return

            # Cargar estado en cada agente
            agents_loaded = 0

            if await self.state_manager.load_agent_state("coder", self.coder_agent):
                agents_loaded += 1

            if await self.state_manager.load_agent_state("code_searcher", self.code_searcher.searcher_agent):
                agents_loaded += 1

            if await self.state_manager.load_agent_state("planning", self.planning_agent):
                agents_loaded += 1

            if await self.state_manager.load_agent_state("summary", self.summary_agent):
                agents_loaded += 1

            self.cli.stop_thinking()

            # Get session metadata and history
            metadata = self.state_manager.get_session_metadata()
            messages = self.state_manager.get_session_history()

            # Display session info
            self.history_viewer.display_session_loaded(
                session_id=session_id,
                total_messages=len(messages),
                agents_restored=agents_loaded
            )

            # Display session metadata
            self.history_viewer.display_session_metadata(metadata, session_id)

            # Display conversation history
            if messages:
                self.cli.print_info("📜 Mostrando historial de conversación:\n")
                self.history_viewer.display_conversation_history(
                    messages=messages,
                    max_messages=20,  # Show last 20 messages
                    show_thoughts=False
                )
                
                if len(messages) > 20:
                    self.cli.print_info(f"💡 Se muestran los últimos 20 de {len(messages)} mensajes")
                    self.cli.print_info("💡 Usa /history --all para ver todos los mensajes")
            else:
                self.cli.print_warning("⚠️ No hay mensajes en el historial de esta sesión")

            self.cli.print_info("\n✅ El agente continuará desde donde quedó la conversación")
            self.logger.info(f"✅ Estado cargado desde sesión: {session_id}")

        except Exception as e:
            self.cli.stop_thinking()
            self.logger.log_error_with_context(e, "_load_state_command")
            self.cli.print_error(f"Error cargando estado: {str(e)}")

    async def _list_sessions_command(self):
        """
        Comando /list-sessions o /sessions: Lista todas las sesiones guardadas con Rich
        """
        try:
            sessions = self.state_manager.list_sessions()

            if not sessions:
                self.history_viewer.display_no_sessions()
                return

            # Display sessions using Rich table
            self.history_viewer.display_sessions_list(sessions)

            self.cli.print_info("💡 Usa /load-session <session_id> para cargar una sesión")
            self.cli.print_info("💡 Usa /history para ver el historial de la sesión actual")

        except Exception as e:
            self.logger.log_error_with_context(e, "_list_sessions_command")
            self.cli.print_error(f"Error listando sesiones: {str(e)}")

    async def _show_history_command(self, parts: list):
        """
        Comando /history: Muestra el historial de la sesión actual

        Uso:
            /history              # Muestra últimos 20 mensajes
            /history --all        # Muestra todos los mensajes
            /history --thoughts   # Incluye pensamientos/razonamientos
            /history <session_id> # Muestra historial de sesión específica
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
                    self.cli.print_warning("⚠️ No hay una sesión activa")
                    self.cli.print_info("💡 Usa /load-session <id> para cargar una sesión")
                    self.cli.print_info("💡 O usa /new-session <título> para crear una nueva")
                    return
                
                messages = self.state_manager.get_session_history()
                metadata = self.state_manager.get_session_metadata()
                session_id = self.state_manager.session_id

            if not messages:
                self.cli.print_warning("⚠️ No hay mensajes en el historial de esta sesión")
                return

            # Display metadata
            self.history_viewer.display_session_metadata(metadata, session_id)

            # Display history
            max_messages = None if show_all else 20
            self.history_viewer.display_conversation_history(
                messages=messages,
                max_messages=max_messages,
                show_thoughts=show_thoughts
            )

            # Show info about truncation
            if not show_all and len(messages) > 20:
                self.cli.print_info(f"\n💡 Se muestran los últimos 20 de {len(messages)} mensajes")
                self.cli.print_info("💡 Usa /history --all para ver todos los mensajes")

        except Exception as e:
            self.logger.log_error_with_context(e, "_show_history_command")
            self.cli.print_error(f"Error mostrando historial: {str(e)}")

    # =========================================================================
    # COMPLEXITY DETECTION - Detección de complejidad de tareas
    # =========================================================================

    async def _detect_task_complexity(self, user_input: str) -> str:
        """
        🔀 ENRUTADOR SIMPLE: Detecta complejidad con llamada directa al modelo.

        NO usa agentes, solo llama al modelo con un prompt optimizado.

        FLUJOS:
        - SIMPLE → SelectorGroupChat (CodeSearcher + Coder)
        - COMPLEX → Planner + TaskExecutor + Agentes

        Returns:
            "simple" o "complex"
        """
        try:
            self.logger.debug(f"🔀 Enrutador: analizando complejidad...")

            # Crear prompt con la solicitud del usuario
            prompt = COMPLEXITY_DETECTOR_PROMPT.format(user_input=user_input)

            # Llamada DIRECTA al modelo (sin agentes, más rápido)
            from autogen_core.models import UserMessage

            result = await self.model_client.create(
                messages=[UserMessage(content=prompt, source="user")]
            )

            # Extraer y parsear respuesta JSON
            response = result.content.strip()
            self.logger.debug(f"🔀 Respuesta del modelo: {response[:200]}")

            # Parsear JSON
            import json
            import re

            try:
                # Limpiar markdown si existe (algunos modelos agregan ```json```)
                json_match = re.search(r'\{[^{}]*"complexity"[^{}]*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    response_data = json.loads(json_str)
                    complexity = response_data.get("complexity", "simple").lower()
                    reasoning = response_data.get("reasoning", "No reasoning provided")

                    self.logger.info(f"✅ Enrutador decidió: {complexity.upper()}")
                    self.logger.debug(f"   Razonamiento: {reasoning}")
                else:
                    # Fallback: buscar la palabra en la respuesta
                    self.logger.warning("⚠️ No se encontró JSON válido, usando fallback")
                    if "complex" in response.lower():
                        complexity = "complex"
                    else:
                        complexity = "simple"
                    self.logger.warning(f"   Fallback decidió: {complexity}")

            except json.JSONDecodeError as e:
                # Si falla el parseo JSON, usar fallback simple
                self.logger.warning(f"⚠️ Error parseando JSON: {e}, usando fallback")
                if "complex" in response.lower():
                    complexity = "complex"
                else:
                    complexity = "simple"
                self.logger.warning(f"   Fallback decidió: {complexity}")

            return complexity

        except Exception as e:
            # Fallback seguro
            self.logger.error(f"❌ Error en enrutador: {str(e)}")
            self.logger.warning("⚠️ Fallback: usando flujo SIMPLE")
            return "simple"

    # =========================================================================
    # CODE SEARCHER - Búsqueda de código
    # =========================================================================

    async def _run_code_searcher(self, query: str):
        """
        Ejecuta CodeSearcher para buscar y analizar código

        Args:
            query: Consulta de búsqueda del usuario
        """
        try:
            self.logger.info(f"🔍 Ejecutando CodeSearcher: {query}")

            # Usar streaming para mostrar progreso en tiempo real
            message_count = 0
            agent_messages_shown = set()

            async for msg in self.code_searcher.search_code_context_stream(query):
                message_count += 1
                msg_type = type(msg).__name__
                self.logger.debug(f"CodeSearcher mensaje #{message_count} - Tipo: {msg_type}")

                if hasattr(msg, 'source') and msg.source != "user":
                    agent_name = msg.source

                    if hasattr(msg, 'content'):
                        content = msg.content
                    else:
                        content = str(msg)

                    # Crear clave única
                    try:
                        if isinstance(content, list):
                            content_str = str(content)
                        else:
                            content_str = content
                        message_key = f"{agent_name}:{hash(content_str)}"
                    except TypeError:
                        message_key = f"{agent_name}:{hash(str(content))}"

                    if message_key not in agent_messages_shown:
                        # Mostrar diferentes tipos de mensajes
                        if msg_type == "ThoughtEvent":
                            self.cli.print_thinking(f"💭 {agent_name}: {content_str}")
                            self.logger.debug(f"💭 Thought: {content_str}")
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallRequestEvent":
                            if isinstance(content, list):
                                for tool_call in content:
                                    if hasattr(tool_call, 'name'):
                                        tool_name = tool_call.name
                                        self.cli.print_info(f"🔧 Buscando con: {tool_name}", agent_name)
                                        self.logger.debug(f"🔧 Tool call: {tool_name}")
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallExecutionEvent":
                            if isinstance(content, list):
                                for execution_result in content:
                                    if hasattr(execution_result, 'name'):
                                        tool_name = execution_result.name
                                        result_preview = str(execution_result.content)[:100] if hasattr(execution_result, 'content') else "OK"
                                        self.cli.print_thinking(f"✅ {agent_name} > {tool_name}: {result_preview}...")
                                        self.logger.debug(f"✅ Tool result: {tool_name}")
                            agent_messages_shown.add(message_key)

                        elif msg_type == "TextMessage":
                            # Mostrar el análisis completo
                            self.cli.print_agent_message(content_str, agent_name)
                            agent_messages_shown.add(message_key)

            self.cli.print_success("\n✅ Búsqueda completada. Usa esta información para tu próxima solicitud.")
            self.logger.info("✅ CodeSearcher completado")

        except Exception as e:
            self.logger.log_error_with_context(e, "_run_code_searcher")
            self.cli.print_error(f"Error en búsqueda de código: {str(e)}")

    # =========================================================================
    # COMPLEX TASK EXECUTION - SelectorGroupChat con selector_func
    # =========================================================================

    async def _execute_complex_task(self, user_input: str):
        """
        Ejecuta tareas complejas usando SelectorGroupChat con re-planificación dinámica.

        ARQUITECTURA:
        - PlanningAgent: Crea plan, revisa progreso, re-planifica
        - CodeSearcher: Busca y analiza código existente
        - Coder: Ejecuta modificaciones, crea archivos
        - SummaryAgent: Crea resumen final

        FLUJO:
        1. Planner crea plan inicial
        2. Selector LLM elige CodeSearcher o Coder para cada tarea
        3. selector_func fuerza a Planner a revisar después de cada acción
        4. Planner puede re-planificar si es necesario
        5. Cuando todo está completo, Planner delega a SummaryAgent
        """
        try:
            self.logger.info("🎯 Usando flujo COMPLEJO: SelectorGroupChat + re-planificación")
            self.cli.print_info("📋 Tarea compleja detectada. Iniciando planificación...\n")

            # Función de selección personalizada para re-planificación dinámica
            def custom_selector_func(messages):
                """
                Controla el flujo para permitir re-planificación:
                - Después de Planner → Selector LLM decide (Coder/CodeSearcher)
                - Después de Coder/CodeSearcher → Volver a Planner (revisar progreso)
                - Si Planner dice DELEGATE_TO_SUMMARY → Ir a SummaryAgent
                """
                if not messages:
                    return None

                last_message = messages[-1]

                # Si el PlanningAgent acaba de hablar
                if last_message.source == "Planner":
                    # Verificar si delegó a summary
                    if "DELEGATE_TO_SUMMARY" in last_message.content:
                        return "SummaryAgent"
                    # De lo contrario, dejar que el selector LLM elija
                    return None  # None = usar selector LLM por defecto

                # Si Coder o CodeSearcher actuaron, SIEMPRE volver a Planner
                # para que revise progreso y actualice el plan
                if last_message.source in ["Coder", "CodeSearcher"]:
                    return "Planner"

                # Para SummaryAgent u otros, usar selector por defecto
                return None

            # Crear equipo complejo con selector_func
            termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(50)

            complex_team = SelectorGroupChat(
                participants=[
                    self.planning_agent,
                    self.code_searcher.searcher_agent,
                    self.coder_agent,
                    self.summary_agent
                ],
                model_client=self.model_client,
                termination_condition=termination,
                selector_func=custom_selector_func  # ← Clave para re-planificación
            )

            # Ejecutar con streaming
            self.logger.debug("Iniciando SelectorGroupChat con streaming...")

            agent_messages_shown = set()
            message_count = 0
            spinner_active = False

            # Start initial spinner
            self.cli.start_thinking(message="iniciando planificación")
            spinner_active = True

            async for msg in complex_team.run_stream(task=user_input):
                message_count += 1
                msg_type = type(msg).__name__

                if hasattr(msg, 'source') and msg.source != "user":
                    agent_name = msg.source

                    if hasattr(msg, 'content'):
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
                        # Mostrar mensajes según tipo
                        if msg_type == "TextMessage":
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            self.cli.print_agent_message(content_str, agent_name)
                            self.logger.debug(f"[{agent_name}] {content_str[:100]}")
                            agent_messages_shown.add(message_key)

                            # After agent finishes, start spinner waiting for next agent
                            self.cli.start_thinking(message=f"esperando siguiente acción")
                            spinner_active = True

                        elif msg_type == "ToolCallRequestEvent":
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)

                            if isinstance(content, list):
                                tool_names = []
                                for tool_call in content:
                                    if hasattr(tool_call, 'name'):
                                        tool_name = tool_call.name
                                        self.cli.print_info(f"🔧 Ejecutando: {tool_name}", agent_name)
                                        tool_names.append(tool_name)

                                # Restart spinner ONCE with first tool name (not in loop)
                                if tool_names:
                                    self.cli.start_thinking(message=f"ejecutando {tool_names[0]}")
                                    spinner_active = True
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallExecutionEvent":
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            if isinstance(content, list):
                                for result in content:
                                    if hasattr(result, 'name'):
                                        tool_name = result.name
                                        result_content = str(result.content) if hasattr(result, 'content') else "OK"

                                        # Check if this is an edit_file result with diff
                                        if tool_name == "edit_file" and "DIFF (Changes Applied)" in result_content:
                                            # Extract and display the diff
                                            diff_start = result_content.find("═══════════════════════════════════════════════════════════════\n📋 DIFF (Changes Applied):")
                                            diff_end = result_content.find("\n═══════════════════════════════════════════════════════════════", diff_start + 100)

                                            if diff_start != -1 and diff_end != -1:
                                                diff_text = result_content[diff_start:diff_end + 64]
                                                # Print file info first
                                                info_end = result_content.find("\n\n", 0, diff_start)
                                                if info_end != -1:
                                                    file_info = result_content[:info_end]
                                                    self.cli.print_thinking(f"✅ {tool_name}: {file_info}")
                                                # Display diff with colors
                                                self.cli.print_diff(diff_text)
                                            else:
                                                # Fallback to showing preview
                                                result_preview = result_content[:100]
                                                self.cli.print_thinking(f"✅ {tool_name}: {result_preview}...")
                                        else:
                                            # Regular tool result
                                            result_preview = result_content[:100]
                                            self.cli.print_thinking(f"✅ {tool_name}: {result_preview}...")

                            self.cli.start_thinking()
                            spinner_active = True
                            agent_messages_shown.add(message_key)

            # Asegurar que el spinner esté detenido
            if spinner_active:
                self.cli.stop_thinking(clear=True)

            # Stop task tracking panel
            if self.cli.task_panel_active:
                self.cli.stop_task_tracking()

            self.logger.info("✅ Flujo complejo completado")
            self.cli.print_success("\n✅ Tarea compleja completada!")

            # 💾 AUTO-SAVE: Guardar estado de agentes automáticamente después de cada respuesta
            await self._auto_save_agent_states()

        except Exception as e:
            if spinner_active:
                self.cli.stop_thinking(clear=True)
            # Stop task tracking on error
            if self.cli.task_panel_active:
                self.cli.stop_task_tracking()
            self.logger.log_error_with_context(e, "_execute_complex_task")
            self.cli.print_error(f"Error en tarea compleja: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    # =========================================================================
    # PROCESAMIENTO DE SOLICITUDES DEL USUARIO
    # =========================================================================

    async def process_user_request(self, user_input: str):
        """
        Procesa una solicitud del usuario con detección inteligente de complejidad.

        FLUJO CONDICIONAL:
        - Tareas SIMPLES → SelectorGroupChat (CodeSearcher/Planner/Coder)
        - Tareas COMPLEJAS → Planner + Executor con re-planificación

        El sistema detecta automáticamente la complejidad basándose en palabras clave
        y la naturaleza de la solicitud.
        """
        try:
            self.logger.info(f"📝 Nueva solicitud del usuario: {user_input[:100]}...")

            # Check if there are mentioned files and add their context
            mentioned_files_content = ""
            if self.cli.mentioned_files:
                self.cli.print_mentioned_files()
                mentioned_files_content = self.cli.get_mentioned_files_content()
                self.logger.info(f"📎 Including {len(self.cli.mentioned_files)} mentioned file(s) in context")

                # Prepend file content to user input
                full_input = f"{mentioned_files_content}\n\nUSER REQUEST:\n{user_input}"
            else:
                full_input = user_input

            # ============= DETECCIÓN DE COMPLEJIDAD =============
            task_complexity = await self._detect_task_complexity(user_input)
            self.logger.info(f"🎯 Complejidad detectada: {task_complexity}")

            # ============= RUTA COMPLEJA: Planner + Executor =============
            if task_complexity == "complex":
                self.logger.info("📋 Usando flujo complejo: Planner + Executor")
                await self._execute_complex_task(user_input)

                # Generar resumen final
                await self._generate_task_summary(user_input)

                # 💾 AUTO-SAVE: Guardar estado después del resumen
                await self._auto_save_agent_states()

                return

            # ============= RUTA SIMPLE: RoundRobinGroupChat =============
            self.logger.info("⚡ Usando flujo SIMPLE: RoundRobinGroupChat (CodeSearcher ↔ Coder)")

            # Crear equipo simple con RoundRobinGroupChat
            termination_simple = TextMentionTermination("TASK_COMPLETED") | MaxMessageTermination(15)

            simple_team = RoundRobinGroupChat(
                participants=[
                    self.code_searcher.searcher_agent,  # Turno 1, 3, 5...
                    self.coder_agent                     # Turno 2, 4, 6...
                ],
                termination_condition=termination_simple
            )

            # Start spinner
            self.cli.start_thinking()
            self.logger.debug("Iniciando RoundRobinGroupChat (CodeSearcher ↔ Coder)")

            agent_messages_shown = set()
            message_count = 0
            spinner_active = True

            # Track para logging
            all_agent_responses = []
            agents_used = []
            tools_called = []

            # Procesar mensajes con streaming
            async for msg in simple_team.run_stream(task=full_input):
                message_count += 1
                msg_type = type(msg).__name__
                self.logger.debug(f"Stream mensaje #{message_count} - Tipo: {msg_type}")

                # Solo procesar mensajes que NO sean del usuario
                if hasattr(msg, 'source') and msg.source != "user":
                    agent_name = msg.source

                    # Track which agents were used
                    if agent_name not in agents_used:
                        agents_used.append(agent_name)

                    # Determinar el contenido del mensaje
                    if hasattr(msg, 'content'):
                        content = msg.content
                    else:
                        content = str(msg)
                        self.logger.warning(f"Mensaje sin atributo 'content'. Usando str(): {content[:100]}...")

                    # Crear clave única para evitar duplicados
                    # Si content es una lista (ej. FunctionCall), convertir a string
                    try:
                        if isinstance(content, list):
                            content_str = str(content)
                        else:
                            content_str = content
                        message_key = f"{agent_name}:{hash(content_str)}"
                    except TypeError:
                        # Si aún no se puede hacer hash, usar un hash del string
                        message_key = f"{agent_name}:{hash(str(content))}"

                    if message_key not in agent_messages_shown:
                        # MOSTRAR DIFERENTES TIPOS DE MENSAJES EN CONSOLA EN TIEMPO REAL
                        if msg_type == "ThoughtEvent":
                            # 💭 Mostrar pensamientos/reflexiones del agente
                            # Stop spinner for thoughts to show them clearly
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False
                            self.cli.print_thinking(f"💭 {agent_name}: {content_str}")
                            self.logger.debug(f"💭 Thought: {content_str}")
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallRequestEvent":
                            # 🔧 Mostrar herramientas que se van a llamar
                            # Stop spinner to show tool call, then restart with specific message
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)

                            if isinstance(content, list):
                                tool_names = []
                                for tool_call in content:
                                    if hasattr(tool_call, 'name'):
                                        tool_name = tool_call.name
                                        tool_args = tool_call.arguments if hasattr(tool_call, 'arguments') else ""
                                        self.cli.print_info(f"🔧 Llamando herramienta: {tool_name}", agent_name)
                                        self.logger.debug(f"🔧 Tool call: {tool_name}({tool_args})")
                                        # Track tools called
                                        if tool_name not in tools_called:
                                            tools_called.append(tool_name)
                                        tool_names.append(tool_name)

                                # Restart spinner ONCE with first tool name (not in loop)
                                if tool_names:
                                    self.cli.start_thinking(message=f"ejecutando {tool_names[0]}")
                                    spinner_active = True
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallExecutionEvent":
                            # ✅ Mostrar resultados de herramientas
                            # Stop spinner to show results
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            if isinstance(content, list):
                                for execution_result in content:
                                    if hasattr(execution_result, 'name'):
                                        tool_name = execution_result.name
                                        result_content = str(execution_result.content) if hasattr(execution_result, 'content') else "OK"

                                        # Check if this is an edit_file result with diff
                                        if tool_name == "edit_file" and "DIFF (Changes Applied)" in result_content:
                                            # Extract and display the diff
                                            diff_start = result_content.find("═══════════════════════════════════════════════════════════════\n📋 DIFF (Changes Applied):")
                                            diff_end = result_content.find("\n═══════════════════════════════════════════════════════════════", diff_start + 100)

                                            if diff_start != -1 and diff_end != -1:
                                                diff_text = result_content[diff_start:diff_end + 64]
                                                # Print file info first
                                                info_end = result_content.find("\n\n", 0, diff_start)
                                                if info_end != -1:
                                                    file_info = result_content[:info_end]
                                                    self.cli.print_thinking(f"✅ {agent_name} > {tool_name}: {file_info}")
                                                # Display diff with colors
                                                self.cli.print_diff(diff_text)
                                                self.logger.debug(f"✅ Tool result: {tool_name} -> DIFF displayed")
                                            else:
                                                # Fallback to showing preview
                                                result_preview = result_content[:100]
                                                self.cli.print_thinking(f"✅ {agent_name} > {tool_name}: {result_preview}...")
                                                self.logger.debug(f"✅ Tool result: {tool_name} -> {result_preview}")
                                        else:
                                            # Regular tool result
                                            result_preview = result_content[:100]
                                            self.cli.print_thinking(f"✅ {agent_name} > {tool_name}: {result_preview}...")
                                            self.logger.debug(f"✅ Tool result: {tool_name} -> {result_preview}")

                            # Restart spinner for next action
                            self.cli.start_thinking()
                            spinner_active = True
                            agent_messages_shown.add(message_key)

                        elif msg_type == "TextMessage":
                            # 💬 Mostrar respuesta final del agente
                            # Stop spinner for final response
                            if spinner_active:
                                self.cli.stop_thinking(clear=True)
                                spinner_active = False

                            preview = content_str[:100] if len(content_str) > 100 else content_str
                            self.logger.log_message_processing(msg_type, agent_name, preview)
                            self.cli.print_agent_message(content_str, agent_name)
                            # Collect agent responses for logging
                            all_agent_responses.append(f"[{agent_name}] {content_str}")
                            agent_messages_shown.add(message_key)

                            # After agent finishes, start spinner waiting for next agent
                            self.cli.start_thinking(message=f"esperando siguiente acción")
                            spinner_active = True

                        else:
                            # Otros tipos de mensaje (para debugging)
                            self.logger.debug(f"Mensaje tipo {msg_type} no mostrado en CLI")

            self.logger.debug(f"✅ Stream completado. Total mensajes procesados: {message_count}")

            # Ensure spinner is stopped
            self.cli.stop_thinking()

            # Log interaction to JSON
            self._log_interaction_to_json(
                user_input=user_input,
                agent_responses=all_agent_responses,
                agents_used=agents_used,
                tools_called=tools_called
            )

            # Generate task completion summary
            await self._generate_task_summary(user_input)

            # 💾 AUTO-SAVE: Guardar estado de agentes automáticamente después de cada respuesta
            await self._auto_save_agent_states()

            # Comprimir historial si es necesario (DISABLED - ya no usamos TaskExecutor)
            # if self.conversation_manager.needs_compression():
            #     self.logger.warning("⚠️ Historial necesita compresión")
            #     # TODO: Implementar compresión directa sin TaskExecutor

            self.logger.info("✅ Solicitud procesada exitosamente")

        except Exception as e:
            # Stop spinner on error
            self.cli.stop_thinking()
            self.logger.log_error_with_context(e, "process_user_request")
            self.cli.print_error(f"Error al procesar solicitud: {str(e)}")
            import traceback
            error_traceback = traceback.format_exc()
            self.logger.error(f"Traceback completo:\n{error_traceback}")
            self.cli.print_error(f"Detalles:\n{error_traceback}")

    # =========================================================================
    # CONVERSATION TRACKING - Log to JSON
    # =========================================================================

    def _log_interaction_to_json(
        self,
        user_input: str,
        agent_responses: list,
        agents_used: list,
        tools_called: list
    ):
        """
        Registra la interacción con el LLM en el archivo JSON y en memoria vectorial

        Args:
            user_input: La solicitud del usuario
            agent_responses: Lista de respuestas de los agentes
            agents_used: Lista de agentes que participaron
            tools_called: Lista de herramientas llamadas
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
                    "total_tools": len(tools_called)
                }
            )

            self.logger.debug(f"📝 Interacción registrada en JSON con ID: {interaction_id}")

            # NUEVO: También guardar en memoria vectorial (async)
            # Esto permite que futuros agentes encuentren conversaciones relevantes
            # ChromaDB solo acepta str, int, float, bool en metadata - convertir listas a strings
            import asyncio
            asyncio.create_task(
                self.memory_manager.add_conversation(
                    user_input=user_input,
                    agent_response=combined_response,
                    metadata={
                        "agents_used": ", ".join(agents_used) if agents_used else "",
                        "tools_called": ", ".join(tools_called) if tools_called else "",
                        "interaction_id": interaction_id,
                        "model": self.settings.model,
                        "provider": provider
                    }
                )
            )

        except Exception as e:
            self.logger.error(f"Error registrando interacción en JSON: {str(e)}")
            # Don't fail the whole request if logging fails

    # =========================================================================
    # TASK SUMMARY - Resumen de tarea completada
    # =========================================================================

    async def _generate_task_summary(self, original_request: str):
        """
        Genera un resumen amigable de la tarea completada

        Args:
            original_request: La solicitud original del usuario
        """
        try:
            self.logger.info("📋 Generando resumen de tarea completada...")

            # Get recent conversation history from StateManager
            messages = self.state_manager.get_session_history()
            
            # Format last 10 messages for context
            recent_messages = ""
            if messages:
                for msg in messages[-10:]:
                    role = msg.get("source", "unknown")
                    content = msg.get("content", "")
                    recent_messages += f"{role}: {content}\n\n"

            # Create summary request
            summary_request = f"""Based on the following conversation, create a brief, friendly summary of what was accomplished.

ORIGINAL REQUEST:
{original_request}

CONVERSATION HISTORY:
{recent_messages}

Create a concise summary (2-5 sentences) explaining what was done to fulfill the user's request."""

            # Run summary agent
            result = await self.summary_agent.run(task=summary_request)

            # Extract summary from result
            summary_text = None
            for message in reversed(result.messages):
                if hasattr(message, 'content') and hasattr(message, 'source'):
                    if message.source != "user":
                        summary_text = message.content
                        break

            if summary_text:
                # Display summary in a special format
                self.cli.print_task_summary(summary_text)
                self.logger.info("✅ Resumen generado exitosamente")
            else:
                # Fallback message
                self.cli.print_success("\n✅ Task completed successfully.")
                self.logger.warning("⚠️ No se pudo generar resumen, usando mensaje por defecto")

        except Exception as e:
            self.logger.error(f"Error generando resumen: {str(e)}")
            # Fail silently with default message
            self.cli.print_success("\n✅ Task completed.")

    # =========================================================================
    # FUNCIONES SIN CAMBIOS
    # =========================================================================

    async def _check_and_resume_session(self):
        """
        Check for previous sessions and offer to resume the most recent one
        """
        try:
            sessions = self.state_manager.list_sessions()
            
            if not sessions:
                # No previous sessions, start fresh
                self.logger.info("No hay sesiones previas, iniciando sesión nueva")
                return

            # Get most recent session
            latest_session = sessions[0]
            session_id = latest_session.get("session_id")
            title = latest_session.get("title", "Sin título")
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
                formatted_date = "Desconocida"

            # Display session info
            self.cli.print_info("\n📋 Sesión anterior encontrada:")
            self.cli.print_info(f"  • Título: {title}")
            self.cli.print_info(f"  • Última interacción: {formatted_date}")
            self.cli.print_info(f"  • Mensajes: {total_messages}")
            
            # Prompt user (use async prompt)
            from prompt_toolkit import PromptSession
            from prompt_toolkit.patch_stdout import patch_stdout
            
            session = PromptSession()
            with patch_stdout():
                response = await session.prompt_async("\n¿Deseas continuar con esta sesión? (S/n): ")
            response = response.strip().lower()

            if response in ['s', 'si', 'sí', 'yes', 'y', '']:
                # Load the session
                self.cli.print_info(f"\n📂 Cargando sesión: {title}...")
                
                # Load state
                loaded = await self.state_manager.load_from_disk(session_id)
                
                if loaded:
                    # Load agents
                    agents_loaded = 0
                    if await self.state_manager.load_agent_state("coder", self.coder_agent):
                        agents_loaded += 1
                    if await self.state_manager.load_agent_state("code_searcher", self.code_searcher.searcher_agent):
                        agents_loaded += 1
                    if await self.state_manager.load_agent_state("planning", self.planning_agent):
                        agents_loaded += 1
                    if await self.state_manager.load_agent_state("summary", self.summary_agent):
                        agents_loaded += 1

                    # Get metadata and messages
                    metadata = self.state_manager.get_session_metadata()
                    messages = self.state_manager.get_session_history()

                    # Display success
                    self.cli.print_success(f"\n✅ Sesión cargada: {title}")
                    self.cli.print_info(f"  • Mensajes restaurados: {len(messages)}")
                    self.cli.print_info(f"  • Agentes restaurados: {agents_loaded}")

                    # Show last few messages
                    if messages:
                        self.cli.print_info("\n📜 Últimos mensajes:")
                        self.history_viewer.display_conversation_history(
                            messages=messages,
                            max_messages=5,  # Show last 5 messages
                            show_thoughts=False
                        )
                        
                        if len(messages) > 5:
                            self.cli.print_info(f"💡 Usa /history para ver todos los {len(messages)} mensajes")

                    self.cli.print_info("\n✅ Puedes continuar la conversación\n")
                else:
                    self.cli.print_error("Error cargando la sesión")
            else:
                self.cli.print_info("\n✨ Iniciando nueva sesión")
                self.cli.print_info("💡 Usa /new-session <título> para crear una sesión con nombre\n")

        except Exception as e:
            self.logger.error(f"Error checking previous sessions: {e}")
            # Continue without loading session

    async def run(self):
        """Ejecuta el loop principal de la CLI"""
        self.logger.info("▶️ Iniciando loop principal de CLI")
        self.cli.print_banner()
        self.cli.print_welcome_message()

        # Check for previous sessions and offer to resume
        await self._check_and_resume_session()

        try:
            while self.running:
                user_input = await self.cli.get_user_input()

                if not user_input:
                    continue

                self.logger.debug(f"Input recibido: {user_input[:100]}")
                self.cli.print_user_message(user_input)

                if user_input.startswith("/"):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        self.logger.info("👋 Usuario solicitó salir")
                        break
                    continue

                await self.process_user_request(user_input)

        except KeyboardInterrupt:
            self.logger.warning("⚠️ Interrupción por teclado (Ctrl+C)")
            self.cli.print_warning("\nInterrumpido por el usuario")

        except Exception as e:
            self.logger.log_error_with_context(e, "main loop")
            self.cli.print_error(f"Error fatal: {str(e)}")

        finally:
            self.logger.info("🔚 Cerrando DaveAgent CLI")
            self.cli.print_goodbye()

            # Cerrar sistema de estado (guarda estado final automáticamente)
            try:
                await self.state_manager.close()
                self.logger.info("✅ Sistema de estado cerrado correctamente")
            except Exception as e:
                self.logger.error(f"Error cerrando estado: {e}")

            # Cerrar sistema de memoria
            try:
                await self.memory_manager.close()
                self.logger.info("✅ Sistema de memoria cerrado correctamente")
            except Exception as e:
                self.logger.error(f"Error cerrando memoria: {e}")

            # Cerrar cliente del modelo
            await self.model_client.close()


async def main(
    debug: bool = False,
    api_key: str = None,
    base_url: str = None,
    model: str = None
):
    """
    Punto de entrada principal

    Args:
        debug: Si True, activa el modo debug con logging detallado
        api_key: API key para el modelo LLM
        base_url: URL base de la API
        model: Nombre del modelo a usar
    """
    app = DaveAgentCLI(debug=debug, api_key=api_key, base_url=base_url, model=model)
    await app.run()


if __name__ == "__main__":
    import sys

    # Detectar si se pasó el flag --debug
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    if debug_mode:
        print("🐛 Modo DEBUG activado")

    asyncio.run(main(debug=debug_mode))