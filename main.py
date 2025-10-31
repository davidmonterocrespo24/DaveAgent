"""
Archivo principal - Interfaz CLI completa del agente de código
"""
import asyncio
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from tools import (
    read_file, write_file, list_dir, run_terminal_cmd,
    codebase_search, grep_search, file_search, delete_file,
    diff_history, edit_file
)
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

        # Herramientas del agente de código
        coder_tools = [
            read_file, write_file, list_dir, run_terminal_cmd,
            edit_file, codebase_search, grep_search, file_search,
            delete_file, diff_history
        ]

        # Crear agente de código con configuración según mejores prácticas de AutoGen
        self.coder_agent = AssistantAgent(
            name="Coder",
            description="Agente experto en desarrollo de software que puede leer/escribir archivos, ejecutar comandos y buscar en el código",
            system_message=AGENT_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=coder_tools,
            max_tool_iterations=5,  # Permitir hasta 5 iteraciones de llamadas a herramientas
            reflect_on_tool_use=False,  # No necesita reflexionar sobre el uso de herramientas
        )

        # Crear componentes del sistema
        self.planner = TaskPlanner(self.model_client)
        self.conversation_manager = ConversationManager(
            max_tokens=8000,
            summary_threshold=6000
        )
        self.cli = CLIInterface()
        self.executor = TaskExecutor(
            coder_agent=self.coder_agent,
            planner=self.planner,
            conversation_manager=self.conversation_manager,
            cli=self.cli,
            model_client=self.model_client
        )

        self.running = True

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
        Procesa una solicitud del usuario completa

        Args:
            user_input: Input del usuario
        """
        try:
            # Agregar al historial
            self.conversation_manager.add_message("user", user_input)

            # Obtener contexto para el planner
            context = self.conversation_manager.get_context_for_agent(max_recent_messages=5)

            # Crear plan de ejecución
            self.cli.print_thinking("Creando plan de ejecución...")
            plan = await self.planner.create_plan(
                user_goal=user_input,
                context=context
            )

            # Agregar plan al historial
            self.conversation_manager.add_message(
                "assistant",
                f"Plan creado: {plan.reasoning}",
                metadata={"plan": plan.model_dump()}
            )

            # Mostrar plan
            self.cli.print_plan(self.planner.get_plan_summary())

            # Preguntar confirmación al usuario
            confirmation = await self.cli.get_user_input(
                "¿Ejecutar este plan? (s/n o presiona Enter para continuar): "
            )

            if confirmation.lower() in ["n", "no"]:
                self.cli.print_info("Plan cancelado por el usuario")
                return

            # Ejecutar el plan
            success = await self.executor.execute_plan()

            # Mensaje final
            if success:
                final_message = f"""
✅ **Objetivo completado exitosamente**

Plan original: {plan.goal}
Tareas completadas: {sum(1 for t in plan.tasks if t.status == 'completed')}
Total de tareas: {len(plan.tasks)}

¿Hay algo más que pueda hacer por ti?
                """
                self.cli.print_agent_message(final_message.strip())
            else:
                self.cli.print_warning(
                    "El plan no se pudo completar totalmente. "
                    "Revisa los errores y proporciona más instrucciones si es necesario."
                )

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
