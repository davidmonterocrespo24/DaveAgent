"""
Archivo principal - Interfaz CLI completa del agente de código
NUEVA ESTRUCTURA REORGANIZADA (CORREGIDA CON LOGGING)
"""
import asyncio
import logging
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
# Importaciones añadidas para el nuevo flujo
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Importar desde nueva estructura
from src.config import (
    AGENT_SYSTEM_PROMPT,
    CODER_AGENT_DESCRIPTION,
    CODER_AGENT_SYSTEM_MESSAGE,
    SELECTOR_PROMPT
)
from src.agents import TaskPlanner, TaskExecutor, CodeSearcher
from src.managers import ConversationManager
from src.interfaces import CLIInterface
from src.utils import get_logger


class CodeAgentCLI:
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
        # Configurar logging
        log_level = logging.DEBUG if debug else logging.INFO
        log_file = f"logs/codeagent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = get_logger(log_file=log_file, level=log_level)

        self.logger.info("🚀 Inicializando CodeAgent CLI")

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

        # Importar todas las herramientas desde la nueva estructura
        from src.tools import (
            # Filesystem
            read_file, write_file, list_dir, edit_file,
            delete_file, file_search,
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
            # Analysis
            analyze_python_file, find_function_definition, list_all_functions,
            codebase_search, grep_search, run_terminal_cmd, diff_history
        )

        coder_tools = [
            # Filesystem (6 tools)
            read_file, write_file, list_dir, edit_file, delete_file, file_search,
            # Git (8 tools)
            git_status, git_add, git_commit, git_push, git_pull, git_log, git_branch, git_diff,
            # JSON (8 tools)
            read_json, write_json, merge_json_files, validate_json,
            format_json, json_get_value, json_set_value, json_to_text,
            # CSV (7 tools)
            read_csv, write_csv, csv_info, filter_csv, merge_csv, csv_to_json, sort_csv,
            # Web (6 tools)
            wiki_search, wiki_summary, wiki_content, wiki_page_info, wiki_random, wiki_set_language,
            # Analysis (7 tools)
            analyze_python_file, find_function_definition, list_all_functions,
            codebase_search, grep_search, run_terminal_cmd, diff_history
        ]

        # Crear agente de código
        self.coder_agent = AssistantAgent(
            name="Coder",
            description=CODER_AGENT_DESCRIPTION,
            system_message=CODER_AGENT_SYSTEM_MESSAGE,
            model_client=self.model_client,
            tools=coder_tools,
            max_tool_iterations=5,
            reflect_on_tool_use=False,
        )

        # Componentes del sistema
        self.conversation_manager = ConversationManager(
            max_tokens=8000,
            summary_threshold=6000
        )
        self.planner = TaskPlanner(self.model_client)
        self.cli = CLIInterface()

        # Crear CodeSearcher con las herramientas de análisis
        search_tools = [
            # Herramientas de búsqueda
            codebase_search, grep_search, file_search,
            # Herramientas de lectura
            read_file, list_dir,
            # Herramientas de análisis Python
            analyze_python_file, find_function_definition, list_all_functions,
        ]
        self.code_searcher = CodeSearcher(self.model_client, search_tools)

        self.executor = TaskExecutor(
            coder_agent=self.coder_agent,
            planner=self.planner,
            conversation_manager=self.conversation_manager,
            cli=self.cli,
            model_client=self.model_client
        )

        # Configurar el equipo de agentes con SelectorGroupChat
        self._setup_team()

        self.running = True

    def _setup_team(self):
        """Configura el equipo de agentes con SelectorGroupChat para orquestación inteligente"""

        # Condición de terminación
        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(30)

        # Crear el team con los 3 agentes: CodeSearcher, Planner, Coder
        self.team = SelectorGroupChat(
            participants=[
                self.code_searcher.searcher_agent,  # Agente de búsqueda
                self.planner.planner_agent,          # Agente de planificación
                self.coder_agent                     # Agente de ejecución
            ],
            model_client=self.model_client,
            termination_condition=termination,
            selector_prompt=SELECTOR_PROMPT,
        )

    async def handle_command(self, command: str) -> bool:
        """Maneja comandos especiales del usuario"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()

        if cmd in ["/exit", "/quit"]:
            return False

        elif cmd == "/help":
            self.cli.print_help()

        elif cmd == "/clear":
            self.conversation_manager.clear()
            self.cli.clear_screen()
            self.cli.print_success("Historial limpiado")

        elif cmd == "/new":
            self.conversation_manager.clear()
            self.planner.current_plan = None
            self.cli.print_success("Nueva conversación iniciada")

        elif cmd == "/plan":
            if self.planner.current_plan:
                self.cli.print_plan(self.planner.get_plan_summary())
            else:
                self.cli.print_info("No hay un plan de ejecución activo")

        elif cmd == "/stats":
            stats = self.conversation_manager.get_statistics()
            self.cli.print_statistics(stats)

        elif cmd == "/save":
            if len(parts) < 2:
                self.cli.print_error("Uso: /save <archivo>")
            else:
                try:
                    self.conversation_manager.save_to_file(parts[1])
                    self.cli.print_success(f"Historial guardado en {parts[1]}")
                except Exception as e:
                    self.cli.print_error(f"Error al guardar: {str(e)}")

        elif cmd == "/load":
            if len(parts) < 2:
                self.cli.print_error("Uso: /load <archivo>")
            else:
                try:
                    self.conversation_manager.load_from_file(parts[1])
                    self.cli.print_success(f"Historial cargado desde {parts[1]}")
                except Exception as e:
                    self.cli.print_error(f"Error al cargar: {str(e)}")

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

        else:
            self.cli.print_error(f"Comando desconocido: {cmd}")
            self.cli.print_info("Usa /help para ver los comandos disponibles")

        return True

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
    # PROCESAMIENTO DE SOLICITUDES DEL USUARIO
    # =========================================================================

    async def process_user_request(self, user_input: str):
        """
        Procesa una solicitud del usuario usando el equipo de agentes (SelectorGroupChat)
        El selector inteligente elige entre CodeSearcher, Planner o Coder según la tarea
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

            self.conversation_manager.add_message("user", full_input)

            self.cli.print_thinking("🤖 Analizando solicitud y seleccionando el mejor agente...")
            self.logger.debug("Iniciando ejecución con SelectorGroupChat (CodeSearcher, Planner, Coder)")

            # USAR run_stream() del TEAM para selección inteligente de agentes
            self.logger.debug("Llamando a team.run_stream() para orquestación inteligente en tiempo real")

            agent_messages_shown = set()  # Para evitar duplicados
            message_count = 0

            # Procesar mensajes conforme llegan del TEAM (STREAMING)
            async for msg in self.team.run_stream(task=full_input):
                message_count += 1
                msg_type = type(msg).__name__
                self.logger.debug(f"Stream mensaje #{message_count} - Tipo: {msg_type}")

                # Solo procesar mensajes que NO sean del usuario
                if hasattr(msg, 'source') and msg.source != "user":
                    agent_name = msg.source

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
                        # Convertir content a string si es necesario para el historial
                        content_for_history = content_str if isinstance(content, list) else content

                        # Guardar en el historial
                        self.conversation_manager.add_message(
                            "assistant",
                            content_for_history,
                            metadata={"agent": agent_name, "type": msg_type}
                        )

                        # MOSTRAR DIFERENTES TIPOS DE MENSAJES EN CONSOLA EN TIEMPO REAL
                        if msg_type == "ThoughtEvent":
                            # 💭 Mostrar pensamientos/reflexiones del agente
                            self.cli.print_thinking(f"💭 {agent_name}: {content_str}")
                            self.logger.debug(f"💭 Thought: {content_str}")
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallRequestEvent":
                            # 🔧 Mostrar herramientas que se van a llamar
                            if isinstance(content, list):
                                for tool_call in content:
                                    if hasattr(tool_call, 'name'):
                                        tool_name = tool_call.name
                                        tool_args = tool_call.arguments if hasattr(tool_call, 'arguments') else ""
                                        self.cli.print_info(f"🔧 Llamando herramienta: {tool_name}", agent_name)
                                        self.logger.debug(f"🔧 Tool call: {tool_name}({tool_args})")
                            agent_messages_shown.add(message_key)

                        elif msg_type == "ToolCallExecutionEvent":
                            # ✅ Mostrar resultados de herramientas
                            if isinstance(content, list):
                                for execution_result in content:
                                    if hasattr(execution_result, 'name'):
                                        tool_name = execution_result.name
                                        result_preview = str(execution_result.content)[:100] if hasattr(execution_result, 'content') else "OK"
                                        # Usar print_thinking en lugar de print_success para mostrar resultado
                                        self.cli.print_thinking(f"✅ {agent_name} > {tool_name}: {result_preview}...")
                                        self.logger.debug(f"✅ Tool result: {tool_name} -> {result_preview}")
                            agent_messages_shown.add(message_key)

                        elif msg_type == "TextMessage":
                            # 💬 Mostrar respuesta final del agente
                            preview = content_str[:100] if len(content_str) > 100 else content_str
                            self.logger.log_message_processing(msg_type, agent_name, preview)
                            self.cli.print_agent_message(content_str, agent_name)
                            agent_messages_shown.add(message_key)

                        else:
                            # Otros tipos de mensaje (para debugging)
                            self.logger.debug(f"Mensaje tipo {msg_type} no mostrado en CLI")

            self.logger.debug(f"✅ Stream completado. Total mensajes procesados: {message_count}")

            # Comprimir historial si es necesario
            if self.conversation_manager.needs_compression():
                self.logger.warning("⚠️ Historial necesita compresión")
                await self.executor._compress_conversation_history()

            self.cli.print_success("\n✅ Tarea completada.")
            self.logger.info("✅ Solicitud procesada exitosamente")

        except Exception as e:
            self.logger.log_error_with_context(e, "process_user_request")
            self.cli.print_error(f"Error al procesar solicitud: {str(e)}")
            import traceback
            error_traceback = traceback.format_exc()
            self.logger.error(f"Traceback completo:\n{error_traceback}")
            self.cli.print_error(f"Detalles:\n{error_traceback}")

    # =========================================================================
    # FUNCIONES SIN CAMBIOS
    # =========================================================================

    async def run(self):
        """Ejecuta el loop principal de la CLI"""
        self.logger.info("▶️ Iniciando loop principal de CLI")
        self.cli.print_banner()
        self.cli.print_welcome_message()

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
            self.logger.info("🔚 Cerrando CodeAgent CLI")
            self.cli.print_goodbye()
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
    app = CodeAgentCLI(debug=debug, api_key=api_key, base_url=base_url, model=model)
    await app.run()


if __name__ == "__main__":
    import sys

    # Detectar si se pasó el flag --debug
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv

    if debug_mode:
        print("🐛 Modo DEBUG activado")

    asyncio.run(main(debug=debug_mode))