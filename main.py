"""
Archivo principal - Interfaz CLI completa del agente de código
NUEVA ESTRUCTURA REORGANIZADA
"""
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Importar desde nueva estructura
from src.config import AGENT_SYSTEM_PROMPT
from src.agents import TaskPlanner, TaskExecutor
from src.managers import ConversationManager
from src.interfaces import CLIInterface


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
                "structured_output": False,
            },
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
            description="""Especialista en tareas de codificación SIMPLES Y DIRECTAS.

Úsalo para:
- Leer, escribir o editar archivos específicos
- Buscar código o archivos
- Corregir errores puntuales
- Operaciones Git (status, commit, push, pull)
- Trabajar con JSON y CSV
- Buscar información en Wikipedia
- Analizar código Python
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
   - Operaciones Git
   - Trabajar con JSON/CSV
   - Buscar en Wikipedia
   - Tareas de 1-3 pasos

   Señales clave: "lee", "busca", "corrige este error", "agrega esta función",
   "qué hace este archivo", "ejecuta", "pequeño cambio", "git status"

FLUJO DE TRABAJO:
- Si la solicitud es ambigua o inicial → Planner (puede delegar a Coder después)
- Si la solicitud es claramente simple → Coder directamente
- Si Planner creó un plan → Coder (para ejecutar tareas)
- Si necesitas usar herramientas → Coder

Lee el historial arriba, analiza la complejidad de la tarea, y selecciona UN agente de {participants}.
"""

        # Condición de terminación
        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(30)

        # Crear el team
        self.team = SelectorGroupChat(
            participants=[self.planner.planner_agent, self.coder_agent],
            model_client=self.model_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
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

        else:
            self.cli.print_error(f"Comando desconocido: {cmd}")
            self.cli.print_info("Usa /help para ver los comandos disponibles")

        return True

    async def process_user_request(self, user_input: str):
        """Procesa una solicitud del usuario usando SelectorGroupChat"""
        try:
            self.conversation_manager.add_message("user", user_input)
            self.cli.print_thinking("Analizando solicitud y seleccionando estrategia...")

            from autogen_agentchat.messages import TextMessage

            result = await self.team.run(
                task=TextMessage(content=user_input, source="user")
            )

            for msg in result.messages:
                if hasattr(msg, 'source') and msg.source != "user":
                    agent_name = msg.source
                    content = msg.content if hasattr(msg, 'content') else str(msg)

                    self.cli.print_agent_message(f"[{agent_name}] {content}")

                    self.conversation_manager.add_message(
                        "assistant",
                        content,
                        metadata={"agent": agent_name}
                    )

            self.cli.print_success("\n✅ Tarea completada")

            if self.conversation_manager.needs_compression():
                self.cli.print_thinking("Comprimiendo historial de conversación...")
                summary = "Historial comprimido automáticamente"
                self.conversation_manager.compress_history(summary)
                self.cli.print_info("Historial comprimido para optimizar memoria")

        except Exception as e:
            self.cli.print_error(f"Error al procesar solicitud: {str(e)}")
            import traceback
            traceback.print_exc()

    async def run(self):
        """Ejecuta el loop principal de la CLI"""
        self.cli.print_banner()
        self.cli.print_welcome_message()

        try:
            while self.running:
                user_input = await self.cli.get_user_input()

                if not user_input:
                    continue

                self.cli.print_user_message(user_input)

                if user_input.startswith("/"):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                await self.process_user_request(user_input)

        except KeyboardInterrupt:
            self.cli.print_warning("\nInterrumpido por el usuario")

        finally:
            self.cli.print_goodbye()
            await self.model_client.close()


async def main():
    """Punto de entrada principal"""
    app = CodeAgentCLI()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
