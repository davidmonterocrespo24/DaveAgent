"""
Archivo principal - Interfaz CLI completa del agente de código
"""
import asyncio
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from prompt import AGENT_SYSTEM_PROMPT
from task_planner import TaskPlanner
from conversation_manager import ConversationManager
from cli_interface import CLIInterface
from task_executor import TaskExecutor


class CodeAgentCLI:
    """Aplicación CLI principal del agente de código"""

    def __init__(self):
        """Inicializa todos los componentes del agente"""
        # Crear cliente del modelo
        self.model_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key="sk-8cb1f4fc5bd74bd3a83f31204b942d60",
            model_capabilities={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": False,  # DeepSeek soporta json_object pero no json_schema
            },
        )

        # Herramientas del agente de código - Importadas desde tools/__init__.py
        from tools import (
            # Herramientas básicas
            read_file, write_file, list_dir, run_terminal_cmd,
            edit_file, codebase_search, grep_search, file_search,
            delete_file, diff_history,
            # Git operations
            git_status, git_add, git_commit, git_push, git_pull,
            git_log, git_branch, git_diff,
            # JSON tools
            read_json, write_json, merge_json_files, validate_json,
            format_json, json_get_value, json_set_value, json_to_text,
            # CSV tools
            read_csv, write_csv, csv_info, filter_csv,
            merge_csv_files as merge_csv, csv_to_json, sort_csv,
            # Wikipedia tools
            wiki_search, wiki_summary, wiki_content,
            wiki_page_info, wiki_random, wiki_set_language,
            # Code analyzer
            analyze_python_file, find_function_definition, list_all_functions
        )

        coder_tools = [
            # Básicas
            read_file, write_file, list_dir, run_terminal_cmd,
            edit_file, codebase_search, grep_search, file_search,
            delete_file, diff_history,
            # Git
            git_status, git_add, git_commit, git_push, git_pull,
            git_log, git_branch, git_diff,
            # JSON
            read_json, write_json, merge_json_files, validate_json,
            format_json, json_get_value, json_set_value, json_to_text,
            # CSV
            read_csv, write_csv, csv_info, filter_csv,
            merge_csv, csv_to_json, sort_csv,
            # Wikipedia
            wiki_search, wiki_summary, wiki_content,
            wiki_page_info, wiki_random, wiki_set_language,
            # Análisis de código
            analyze_python_file, find_function_definition, list_all_functions
        ]

        # Crear agente de código con descripción optimizada para el selector
        self.coder_agent = AssistantAgent(
            name="Coder",
            description="""Especialista en tareas de codificación SIMPLES Y DIRECTAS.

Úsalo para:
- Leer, escribir o editar archivos específicos
- Buscar código o archivos
- Corregir errores puntuales
- Crear scripts o funciones simples
- Tareas que se completan en 1-3 pasos

NO lo uses para:
- Proyectos complejos que requieren múltiples archivos
- Tareas que necesitan planificación detallada
- Implementaciones completas de sistemas""",
            system_message=AGENT_SYSTEM_PROMPT,
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

        # Selector prompt: El cerebro de la orquestación
        # Analiza la complejidad y selecciona el agente apropiado
        selector_prompt = """Selecciona el agente más apropiado para la siguiente tarea.

{roles}

Contexto de la conversación:
{history}

CRITERIOS DE SELECCIÓN:

1. **Planner** - Para tareas COMPLEJAS que requieren:
   - Múltiples archivos o componentes
   - Sistemas completos o aplicaciones
   - Refactorización mayor
   - Arquitectura o diseño de soluciones
   - Proyectos que necesitan planificación estructurada

   Señales clave: "sistema", "aplicación", "proyecto completo", "múltiples archivos",
   "crear desde cero", "refactorizar todo"

2. **Coder** - Para tareas SIMPLES Y DIRECTAS:
   - Leer o buscar archivos específicos
   - Editar 1-3 archivos
   - Corregir un bug puntual
   - Agregar una función simple
   - Ejecutar comandos del sistema
   - Tareas de 1-3 pasos

   Señales clave: "lee", "busca", "corrige este error", "agrega esta función",
   "qué hace este archivo", "ejecuta", "pequeño cambio"

FLUJO DE TRABAJO:
- Si la solicitud es ambigua o inicial → Planner (puede delegar a Coder después)
- Si la solicitud es claramente simple → Coder directamente
- Si Planner creó un plan → Coder (para ejecutar tareas)
- Si necesitas usar herramientas (read_file, write_file, etc.) → Coder

Lee el historial arriba, analiza la complejidad de la tarea, y selecciona UN agente de {participants}.
"""

        # Condición de terminación
        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(30)

        # Crear el team con solo Planner y Coder
        # El selector_prompt maneja la orquestación inteligente
        self.team = SelectorGroupChat(
            participants=[self.planner.planner_agent, self.coder_agent],
            model_client=self.model_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
        )

    async def handle_command(self, command: str) -> bool:
        """
        Maneja comandos especiales del usuario

        Args:
            command: Comando a ejecutar

        Returns:
            True si debe continuar, False si debe salir
        """
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
            # Limpiar historial y plan actual
            self.conversation_manager.clear()
            self.planner.current_plan = None
            self.cli.print_success("Nueva conversación iniciada - Historial y plan limpiados")
            self.cli.print_info(
                "Comenzando desde cero. El agente no tiene contexto de conversaciones anteriores.",
                "Nueva Sesión"
            )

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
                    filepath = parts[1]
                    self.conversation_manager.save_to_file(filepath)
                    self.cli.print_success(f"Historial guardado en {filepath}")
                except Exception as e:
                    self.cli.print_error(f"Error al guardar: {str(e)}")

        elif cmd == "/load":
            if len(parts) < 2:
                self.cli.print_error("Uso: /load <archivo>")
            else:
                try:
                    filepath = parts[1]
                    self.conversation_manager.load_from_file(filepath)
                    self.cli.print_success(f"Historial cargado desde {filepath}")
                except Exception as e:
                    self.cli.print_error(f"Error al cargar: {str(e)}")

        else:
            self.cli.print_error(f"Comando desconocido: {cmd}")
            self.cli.print_info("Usa /help para ver los comandos disponibles")

        return True

    async def process_user_request(self, user_input: str):
        """
        Procesa una solicitud del usuario usando SelectorGroupChat

        Args:
            user_input: Input del usuario
        """
        try:
            # Agregar al historial
            self.conversation_manager.add_message("user", user_input)

            # Mostrar que está procesando
            self.cli.print_thinking("Analizando solicitud y seleccionando estrategia...")

            # Ejecutar el team con SelectorGroupChat
            # El selector decidirá si usar Planner o Coder
            from autogen_agentchat.messages import TextMessage

            result = await self.team.run(
                task=TextMessage(content=user_input, source="user")
            )

            # Procesar los mensajes de la conversación
            for msg in result.messages:
                # Agregar mensaje al historial
                if hasattr(msg, 'source') and msg.source != "user":
                    agent_name = msg.source
                    content = msg.content if hasattr(msg, 'content') else str(msg)

                    # Mostrar mensaje del agente
                    self.cli.print_agent_message(f"[{agent_name}] {content}")

                    # Guardar en historial
                    self.conversation_manager.add_message(
                        "assistant",
                        content,
                        metadata={"agent": agent_name}
                    )

            # Mensaje final
            self.cli.print_success("\n✅ Tarea completada")

            # Comprimir historial si es necesario
            if self.conversation_manager.needs_compression():
                self.cli.print_thinking("Comprimiendo historial de conversación...")
                # Aquí podrías usar el LLM para crear un resumen
                summary = "Historial comprimido automáticamente"
                self.conversation_manager.compress_history(summary)
                self.cli.print_info("Historial comprimido para optimizar memoria")

        except Exception as e:
            self.cli.print_error(f"Error al procesar solicitud: {str(e)}")
            import traceback
            traceback.print_exc()

    async def run(self):
        """Ejecuta el loop principal de la CLI"""
        # Mostrar banner y bienvenida
        self.cli.print_banner()
        self.cli.print_welcome_message()

        try:
            while self.running:
                # Obtener input del usuario
                user_input = await self.cli.get_user_input()

                if not user_input:
                    continue

                # Mostrar mensaje del usuario
                self.cli.print_user_message(user_input)

                # Verificar si es un comando
                if user_input.startswith("/"):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Procesar como solicitud normal
                await self.process_user_request(user_input)

        except KeyboardInterrupt:
            self.cli.print_warning("\nInterrumpido por el usuario")

        finally:
            # Limpieza
            self.cli.print_goodbye()
            await self.model_client.close()


async def main():
    """Punto de entrada principal"""
    app = CodeAgentCLI()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
