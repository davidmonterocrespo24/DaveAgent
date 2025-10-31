"""
Ejecutor de tareas con re-planificación dinámica
"""
from typing import Optional, List, Dict, Any
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import TextMessage, ToolCallRequestEvent, ToolCallExecutionEvent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from .task_planner import TaskPlanner, Task, ExecutionPlan
from ..managers.conversation_manager import ConversationManager
from ..interfaces.cli_interface import CLIInterface
import asyncio
from datetime import datetime


class TaskExecutor:
    """Ejecuta tareas del plan usando el agente de código con re-planificación dinámica"""

    def __init__(
        self,
        coder_agent: AssistantAgent,
        planner: TaskPlanner,
        conversation_manager: ConversationManager,
        cli: CLIInterface,
        model_client: OpenAIChatCompletionClient
    ):
        """
        Args:
            coder_agent: Agente de código configurado con herramientas
            planner: Sistema de planificación de tareas
            conversation_manager: Gestor del historial de conversaciones
            cli: Interfaz CLI para mostrar mensajes
            model_client: Cliente del modelo para crear resúmenes
        """
        self.coder_agent = coder_agent
        self.planner = planner
        self.conversation_manager = conversation_manager
        self.cli = cli
        self.model_client = model_client

        # Configurar equipo para el agente
        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(15)
        self.team = RoundRobinGroupChat([coder_agent], termination_condition=termination)

        # Agente para crear resúmenes del historial
        self.summarizer_agent = AssistantAgent(
            name="Summarizer",
            model_client=model_client,
            system_message="Eres un experto en crear resúmenes concisos de conversaciones técnicas.",
        )

    async def execute_task(self, task: Task) -> tuple[bool, str, Optional[str]]:
        """
        Ejecuta una tarea individual

        Args:
            task: Tarea a ejecutar

        Returns:
            Tupla (éxito, resultado, mensaje_error)
        """
        try:
            # Marcar tarea como en progreso
            self.planner.update_task_status(task.id, "in_progress")

            # Mostrar en CLI
            self.cli.print_task_start(task.id, task.title, task.description)

            # Obtener contexto de conversación
            context = self.conversation_manager.get_context_for_agent(max_recent_messages=8)

            # Construir el prompt para el agente
            task_prompt = f"""CONTEXTO DE LA CONVERSACIÓN:
{context}

TAREA A REALIZAR:
{task.description}

Ejecuta esta tarea utilizando las herramientas disponibles. Al finalizar, proporciona un resumen claro de lo realizado."""

            # Ejecutar el agente
            result = await self.team.run(task=task_prompt)

            # Procesar resultado
            result_text = self._extract_result_from_messages(result.messages)

            # Agregar al historial
            self.conversation_manager.add_message(
                "assistant",
                f"Tarea {task.id} ejecutada: {result_text}",
                metadata={"task_id": task.id, "task_title": task.title}
            )

            # Actualizar estado
            self.planner.update_task_status(task.id, "completed", result=result_text)

            # Mostrar en CLI
            self.cli.print_task_complete(task.id, task.title, result_text)

            return True, result_text, None

        except Exception as e:
            error_msg = str(e)

            # Agregar error al historial
            self.conversation_manager.add_message(
                "system",
                f"Error en tarea {task.id}: {error_msg}",
                metadata={"task_id": task.id, "error": True}
            )

            # Actualizar estado
            self.planner.update_task_status(task.id, "failed", error=error_msg)

            # Mostrar en CLI
            self.cli.print_task_failed(task.id, task.title, error_msg)

            return False, "", error_msg

    def _extract_result_from_messages(self, messages: List) -> str:
        """Extrae el resultado relevante de los mensajes del agente"""
        result_parts = []

        for message in messages:
            if isinstance(message, TextMessage) and message.source != "user":
                result_parts.append(message.content)
            elif isinstance(message, ToolCallExecutionEvent):
                # Incluir resultados de herramientas
                for execution_result in message.content:
                    if hasattr(execution_result, 'content'):
                        result_parts.append(f"Herramienta ejecutada: {execution_result.content[:200]}")

        if not result_parts:
            return "Tarea ejecutada sin salida específica"

        # Tomar el último mensaje relevante
        return result_parts[-1] if result_parts else "Sin resultado"

    async def execute_plan(self) -> bool:
        """
        Ejecuta el plan completo con re-planificación dinámica

        Returns:
            True si se completó exitosamente, False si hay errores
        """
        if not self.planner.current_plan:
            self.cli.print_error("No hay un plan de ejecución activo")
            return False

        # Mostrar el plan inicial
        self.cli.print_plan(self.planner.get_plan_summary())

        max_iterations = 50  # Prevenir loops infinitos
        iteration = 0

        while not self.planner.is_plan_complete() and iteration < max_iterations:
            iteration += 1

            # Verificar si necesitamos comprimir el historial
            if self.conversation_manager.needs_compression():
                await self._compress_conversation_history()

            # Obtener siguiente tarea
            next_task = self.planner.get_next_task()

            if not next_task:
                # No hay tareas pendientes disponibles
                # Verificar si hay tareas bloqueadas o fallidas
                has_blocked = any(
                    t.status in ["blocked", "failed"]
                    for t in self.planner.current_plan.tasks
                )

                if has_blocked:
                    self.cli.print_warning(
                        "Hay tareas bloqueadas o fallidas. El plan no puede continuar."
                    )
                    return False
                else:
                    # Todas las tareas completadas
                    break

            # Ejecutar la tarea
            success, result, error = await self.execute_task(next_task)

            # Determinar si necesitamos re-planificar
            should_replan = False

            if not success:
                # Tarea falló, necesitamos re-planificar
                should_replan = True
            elif self._result_suggests_replanning(result):
                # El resultado sugiere que el plan debe cambiar
                should_replan = True

            # Re-planificar si es necesario
            if should_replan:
                await self._replan_based_on_result(next_task.id, success, result, error)

            # Pequeña pausa para no saturar
            await asyncio.sleep(0.5)

        # Verificar si se completó
        if self.planner.is_plan_complete():
            completed_successfully = all(
                t.status == "completed"
                for t in self.planner.current_plan.tasks
            )

            if completed_successfully:
                self.cli.print_success("¡Plan de ejecución completado exitosamente!")
                return True
            else:
                self.cli.print_warning("El plan finalizó con algunas tareas fallidas")
                return False
        else:
            self.cli.print_error(f"Se alcanzó el límite de iteraciones ({max_iterations})")
            return False

    def _result_suggests_replanning(self, result: str) -> bool:
        """Determina si un resultado sugiere que debemos re-planificar"""
        # Palabras clave que sugieren problemas o cambios
        keywords = [
            "error", "fallo", "no encontrado", "no existe",
            "inesperado", "necesario", "requiere", "falta",
            "adicional", "primero", "antes"
        ]

        result_lower = result.lower()
        return any(keyword in result_lower for keyword in keywords)

    async def _replan_based_on_result(
        self,
        task_id: int,
        success: bool,
        result: str,
        error: Optional[str]
    ):
        """Re-planifica basándose en el resultado de una tarea"""
        try:
            self.cli.print_thinking("Analizando resultado y actualizando plan...")

            # Solicitar actualización del plan
            plan_update = await self.planner.update_plan(
                task_result=result,
                task_id=task_id,
                success=success,
                error_message=error
            )

            # Mostrar cambios en CLI
            if plan_update.new_tasks or plan_update.modified_tasks or plan_update.removed_task_ids:
                changes_summary = self._format_plan_changes(plan_update)
                self.cli.print_plan_update(plan_update.reasoning, changes_summary)

                # Mostrar plan actualizado
                self.cli.print_plan(self.planner.get_plan_summary())

        except Exception as e:
            self.cli.print_error(f"Error al actualizar el plan: {str(e)}")

    def _format_plan_changes(self, plan_update) -> str:
        """Formatea los cambios del plan para mostrar"""
        changes = []

        if plan_update.new_tasks:
            changes.append(f"• {len(plan_update.new_tasks)} tarea(s) nueva(s) añadida(s)")

        if plan_update.modified_tasks:
            changes.append(f"• {len(plan_update.modified_tasks)} tarea(s) modificada(s)")

        if plan_update.removed_task_ids:
            changes.append(f"• {len(plan_update.removed_task_ids)} tarea(s) eliminada(s)")

        return "\n".join(changes) if changes else "Sin cambios"

    async def _compress_conversation_history(self):
        """Comprime el historial de conversación cuando crece demasiado"""
        try:
            self.cli.print_thinking("Comprimiendo historial de conversación...")

            # Obtener prompt para resumen
            summary_prompt = self.conversation_manager.create_summary_prompt()

            # Crear resumen usando el agente
            result = await self.summarizer_agent.run(task=summary_prompt)

            # Extraer el resumen del resultado
            summary_text = ""
            for message in result.messages:
                if isinstance(message, TextMessage) and message.source != "user":
                    summary_text = message.content
                    break

            if summary_text:
                # Aplicar compresión
                self.conversation_manager.compress_history(summary_text)

                stats = self.conversation_manager.get_statistics()
                self.cli.print_info(
                    f"Historial comprimido. Tokens actuales: {stats['total_tokens']}",
                    "Compresión"
                )

        except Exception as e:
            self.cli.print_warning(f"No se pudo comprimir el historial: {str(e)}")
