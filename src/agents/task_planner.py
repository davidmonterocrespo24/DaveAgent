"""
Sistema de planificación y gestión de tareas con agente planner
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, StructuredMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from datetime import datetime
import json
from src.config import (
    TASK_PLANNER_DESCRIPTION,
    TASK_PLANNER_SYSTEM_MESSAGE,
    TASK_PLANNER_UPDATER_MESSAGE
)


class Task(BaseModel):
    """Representa una tarea individual en el plan"""
    id: int
    title: str
    description: str
    status: Literal["pending", "in_progress", "completed", "failed", "blocked"]
    dependencies: List[int] = []
    result: Optional[str] = None
    error: Optional[str] = None


class ExecutionPlan(BaseModel):
    """Plan de ejecución completo con lista de tareas"""
    goal: str
    tasks: List[Task]
    reasoning: str
    estimated_complexity: Literal["low", "medium", "high", "very_high"]


class PlanUpdate(BaseModel):
    """Actualización del plan basada en resultados de ejecución"""
    reasoning: str
    modified_tasks: List[Task]
    new_tasks: List[Task] = []
    removed_task_ids: List[int] = []


class TaskPlanner:
    """Gestiona la creación y actualización de planes de ejecución"""

    def __init__(self, model_client: OpenAIChatCompletionClient):
        """
        Args:
            model_client: Cliente del modelo para el agente planner
        """
        self.model_client = model_client

        # Crear el agente planner SIN output estructurado (para compatibilidad con DeepSeek)
        # Siguiendo mejores prácticas de AutoGen: incluir description clara para el selector
        self.planner_agent = AssistantAgent(
            name="Planner",
            description=TASK_PLANNER_DESCRIPTION,
            model_client=model_client,
            system_message=TASK_PLANNER_SYSTEM_MESSAGE,
            # NO usar output_content_type porque DeepSeek no soporta structured_output
        )

        # Agente para actualizar planes
        self.plan_updater_agent = AssistantAgent(
            name="PlanUpdater",
            description="Agent specialized in adapting execution plans based on results and errors",
            model_client=model_client,
            system_message=TASK_PLANNER_UPDATER_MESSAGE,
            # NO usar output_content_type porque DeepSeek no soporta structured_output
        )

        self.current_plan: Optional[ExecutionPlan] = None

    async def create_plan(self, user_goal: str, context: str = "") -> ExecutionPlan:
        """
        Crea un nuevo plan de ejecución basado en el objetivo del usuario

        Args:
            user_goal: Objetivo o solicitud del usuario
            context: Contexto adicional (historial, estado del proyecto, etc.)

        Returns:
            ExecutionPlan con las tareas planificadas
        """
        planning_prompt = f"""OBJETIVO DEL USUARIO:
{user_goal}

CONTEXTO ADICIONAL:
{context if context else 'Sin contexto adicional'}

Crea un plan de ejecución detallado para lograr este objetivo."""

        result = await self.planner_agent.run(task=planning_prompt)

        # Extraer el texto del último mensaje
        plan_text = None
        for message in reversed(result.messages):
            if isinstance(message, TextMessage) and message.source != "user":
                plan_text = message.content
                break

        if not plan_text:
            raise Exception("No se recibió respuesta del agente planner")

        # Parsear el JSON
        try:
            # Limpiar el texto (quitar markdown code blocks si los hay)
            plan_text = plan_text.strip()
            if plan_text.startswith("```json"):
                plan_text = plan_text[7:]
            if plan_text.startswith("```"):
                plan_text = plan_text[3:]
            if plan_text.endswith("```"):
                plan_text = plan_text[:-3]
            plan_text = plan_text.strip()

            # Parsear JSON
            plan_dict = json.loads(plan_text)

            # Crear el ExecutionPlan desde el diccionario
            self.current_plan = ExecutionPlan(**plan_dict)
            return self.current_plan

        except json.JSONDecodeError as e:
            raise Exception(f"Error parseando JSON del plan: {e}\nTexto recibido: {plan_text[:500]}")
        except Exception as e:
            raise Exception(f"Error creando plan: {e}")

    async def update_plan(
        self,
        task_result: str,
        task_id: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> PlanUpdate:
        """
        Actualiza el plan basándose en el resultado de una tarea

        Args:
            task_result: Resultado de la tarea ejecutada
            task_id: ID de la tarea ejecutada
            success: Si la tarea fue exitosa
            error_message: Mensaje de error si la tarea falló

        Returns:
            PlanUpdate con las modificaciones al plan
        """
        if not self.current_plan:
            raise Exception("No hay un plan actual para actualizar")

        # Encontrar la tarea ejecutada
        executed_task = None
        for task in self.current_plan.tasks:
            if task.id == task_id:
                executed_task = task
                break

        if not executed_task:
            raise Exception(f"Tarea {task_id} no encontrada en el plan actual")

        update_prompt = f"""PLAN ACTUAL:
Objetivo: {self.current_plan.goal}
Tareas totales: {len(self.current_plan.tasks)}

TAREA EJECUTADA:
ID: {executed_task.id}
Título: {executed_task.title}
Descripción: {executed_task.description}

RESULTADO:
Éxito: {success}
Resultado: {task_result}
{f'Error: {error_message}' if error_message else ''}

PLAN COMPLETO (JSON):
{json.dumps([task.model_dump() for task in self.current_plan.tasks], indent=2, ensure_ascii=False)}

Basándote en este resultado, determina si el plan necesita actualizarse.
Si la tarea fue exitosa y todo va según lo planeado, devuelve listas vacías.
Si necesitas cambios, especifica qué tareas modificar, añadir o eliminar."""

        result = await self.plan_updater_agent.run(task=update_prompt)

        # Extraer el texto del último mensaje
        update_text = None
        for message in reversed(result.messages):
            if isinstance(message, TextMessage) and message.source != "user":
                update_text = message.content
                break

        if not update_text:
            raise Exception("No se recibió respuesta del agente updater")

        # Parsear el JSON
        try:
            # Limpiar el texto
            update_text = update_text.strip()
            if update_text.startswith("```json"):
                update_text = update_text[7:]
            if update_text.startswith("```"):
                update_text = update_text[3:]
            if update_text.endswith("```"):
                update_text = update_text[:-3]
            update_text = update_text.strip()

            # Parsear JSON
            update_dict = json.loads(update_text)

            # Crear el PlanUpdate desde el diccionario
            plan_update = PlanUpdate(**update_dict)

            # Aplicar la actualización al plan actual
            self._apply_plan_update(plan_update)
            return plan_update

        except json.JSONDecodeError as e:
            raise Exception(f"Error parseando JSON de actualización: {e}\nTexto recibido: {update_text[:500]}")
        except Exception as e:
            raise Exception(f"Error creando actualización: {e}")

    def _apply_plan_update(self, update: PlanUpdate):
        """Aplica una actualización al plan actual"""
        if not self.current_plan:
            return

        # Eliminar tareas marcadas para eliminación
        self.current_plan.tasks = [
            task for task in self.current_plan.tasks
            if task.id not in update.removed_task_ids
        ]

        # Actualizar tareas modificadas
        for modified_task in update.modified_tasks:
            for i, task in enumerate(self.current_plan.tasks):
                if task.id == modified_task.id:
                    self.current_plan.tasks[i] = modified_task
                    break

        # Añadir nuevas tareas
        if update.new_tasks:
            # Encontrar el ID máximo actual
            max_id = max([task.id for task in self.current_plan.tasks], default=0)
            for i, new_task in enumerate(update.new_tasks):
                # Reasignar IDs para evitar conflictos
                new_task.id = max_id + i + 1
            self.current_plan.tasks.extend(update.new_tasks)

    def get_next_task(self) -> Optional[Task]:
        """Obtiene la siguiente tarea pendiente que se puede ejecutar"""
        if not self.current_plan:
            return None

        for task in self.current_plan.tasks:
            if task.status != "pending":
                continue

            # Verificar que todas las dependencias estén completadas
            dependencies_met = True
            for dep_id in task.dependencies:
                for dep_task in self.current_plan.tasks:
                    if dep_task.id == dep_id and dep_task.status != "completed":
                        dependencies_met = False
                        break

            if dependencies_met:
                return task

        return None

    def update_task_status(
        self,
        task_id: int,
        status: Literal["pending", "in_progress", "completed", "failed", "blocked"],
        result: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Actualiza el estado de una tarea"""
        if not self.current_plan:
            return

        for task in self.current_plan.tasks:
            if task.id == task_id:
                task.status = status
                if result:
                    task.result = result
                if error:
                    task.error = error
                break

    def get_plan_summary(self) -> str:
        """Obtiene un resumen del plan actual"""
        if not self.current_plan:
            return "No hay plan activo"

        completed = sum(1 for t in self.current_plan.tasks if t.status == "completed")
        failed = sum(1 for t in self.current_plan.tasks if t.status == "failed")
        in_progress = sum(1 for t in self.current_plan.tasks if t.status == "in_progress")
        pending = sum(1 for t in self.current_plan.tasks if t.status == "pending")

        summary = f"""=== PLAN DE EJECUCIÓN ===
Objetivo: {self.current_plan.goal}
Complejidad: {self.current_plan.estimated_complexity}
Razonamiento: {self.current_plan.reasoning}

Progreso:
  ✓ Completadas: {completed}
  ⚡ En progreso: {in_progress}
  ○ Pendientes: {pending}
  ✗ Fallidas: {failed}
  Total: {len(self.current_plan.tasks)}

Tareas:
"""
        for task in self.current_plan.tasks:
            status_icon = {
                "completed": "✓",
                "in_progress": "⚡",
                "pending": "○",
                "failed": "✗",
                "blocked": "⊘"
            }.get(task.status, "?")

            summary += f"  {status_icon} [{task.id}] {task.title}\n"
            if task.status == "in_progress":
                summary += f"      {task.description}\n"

        return summary

    def is_plan_complete(self) -> bool:
        """Verifica si todas las tareas del plan están completadas"""
        if not self.current_plan:
            return True

        return all(
            task.status in ["completed", "failed"]
            for task in self.current_plan.tasks
        )

    def get_plan_json(self) -> str:
        """Obtiene el plan en formato JSON"""
        if not self.current_plan:
            return "{}"
        return self.current_plan.model_dump_json(indent=2, exclude_none=True)
