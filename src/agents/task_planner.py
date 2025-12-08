"""
Task planning and management system with planner agent
"""
import json
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, StructuredMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal

from src.config import (
    TASK_PLANNER_DESCRIPTION,
    TASK_PLANNER_SYSTEM_MESSAGE,
    TASK_PLANNER_UPDATER_MESSAGE
)


class Task(BaseModel):
    """Represents an individual task in the plan"""
    id: int
    title: str
    description: str
    status: Literal["pending", "in_progress", "completed", "failed", "blocked"]
    dependencies: List[int] = []
    result: Optional[str] = None
    error: Optional[str] = None


class ExecutionPlan(BaseModel):
    """Complete execution plan with task list"""
    goal: str
    tasks: List[Task]
    reasoning: str
    estimated_complexity: Literal["low", "medium", "high", "very_high"]


class PlanUpdate(BaseModel):
    """Plan update based on execution results"""
    reasoning: str
    modified_tasks: List[Task]
    new_tasks: List[Task] = []
    removed_task_ids: List[int] = []


class TaskPlanner:
    """Manages the creation and updating of execution plans"""

    def __init__(self, model_client: OpenAIChatCompletionClient):
        """
        Args:
            model_client: Model client for the planner agent
        """
        self.model_client = model_client

        # Create planner agent WITHOUT structured output (for DeepSeek compatibility)
        # Following AutoGen best practices: include clear description for selector
        self.planner_agent = AssistantAgent(
            name="Planner",
            description=TASK_PLANNER_DESCRIPTION,
            model_client=model_client,
            system_message=TASK_PLANNER_SYSTEM_MESSAGE,
            # DO NOT use output_content_type because DeepSeek doesn't support structured_output
        )

        # Agent for updating plans
        self.plan_updater_agent = AssistantAgent(
            name="PlanUpdater",
            description="Agent specialized in adapting execution plans based on results and errors",
            model_client=model_client,
            system_message=TASK_PLANNER_UPDATER_MESSAGE,
            # DO NOT use output_content_type because DeepSeek doesn't support structured_output
        )

        self.current_plan: Optional[ExecutionPlan] = None

    async def create_plan(self, user_goal: str, context: str = "") -> ExecutionPlan:
        """
        Creates a new execution plan based on the user's goal

        Args:
            user_goal: User's goal or request
            context: Additional context (history, project state, etc.)

        Returns:
            ExecutionPlan with the planned tasks
        """
        planning_prompt = f"""USER GOAL:
{user_goal}

ADDITIONAL CONTEXT:
{context if context else 'No additional context'}

Create a detailed execution plan to achieve this goal."""

        result = await self.planner_agent.run(task=planning_prompt)

        # Extract text from the last message
        plan_text = None
        for message in reversed(result.messages):
            if isinstance(message, TextMessage) and message.source != "user":
                plan_text = message.content
                break

        if not plan_text:
            raise Exception("No response received from planner agent")

        # Parse the JSON
        try:
            # Clean the text (remove markdown code blocks if present)
            plan_text = plan_text.strip()
            if plan_text.startswith("```json"):
                plan_text = plan_text[7:]
            if plan_text.startswith("```"):
                plan_text = plan_text[3:]
            if plan_text.endswith("```"):
                plan_text = plan_text[:-3]
            plan_text = plan_text.strip()

            # Parse JSON
            plan_dict = json.loads(plan_text)

            # Create ExecutionPlan from dictionary
            self.current_plan = ExecutionPlan(**plan_dict)
            return self.current_plan

        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing plan JSON: {e}\nReceived text: {plan_text[:500]}")
        except Exception as e:
            raise Exception(f"Error creating plan: {e}")

    async def update_plan(
            self,
            task_result: str,
            task_id: int,
            success: bool,
            error_message: Optional[str] = None
    ) -> PlanUpdate:
        """
        Updates the plan based on a task's result

        Args:
            task_result: Result of the executed task
            task_id: ID of the executed task
            success: Whether the task was successful
            error_message: Error message if the task failed

        Returns:
            PlanUpdate with modifications to the plan
        """
        if not self.current_plan:
            raise Exception("No current plan to update")

        # Find the executed task
        executed_task = None
        for task in self.current_plan.tasks:
            if task.id == task_id:
                executed_task = task
                break

        if not executed_task:
            raise Exception(f"Task {task_id} not found in current plan")

        update_prompt = f"""CURRENT PLAN:
Goal: {self.current_plan.goal}
Total tasks: {len(self.current_plan.tasks)}

EXECUTED TASK:
ID: {executed_task.id}
Title: {executed_task.title}
Description: {executed_task.description}

RESULT:
Success: {success}
Result: {task_result}
{f'Error: {error_message}' if error_message else ''}

COMPLETE PLAN (JSON):
{json.dumps([task.model_dump() for task in self.current_plan.tasks], indent=2, ensure_ascii=False)}

Based on this result, determine if the plan needs to be updated.
If the task was successful and everything is going as planned, return empty lists.
If changes are needed, specify which tasks to modify, add, or remove."""

        result = await self.plan_updater_agent.run(task=update_prompt)

        # Extract text from the last message
        update_text = None
        for message in reversed(result.messages):
            if isinstance(message, TextMessage) and message.source != "user":
                update_text = message.content
                break

        if not update_text:
            raise Exception("No response received from updater agent")

        # Parse the JSON
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

            # Parse JSON
            update_dict = json.loads(update_text)

            # Create PlanUpdate from dictionary
            plan_update = PlanUpdate(**update_dict)

            # Apply the update to the current plan
            self._apply_plan_update(plan_update)
            return plan_update

        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing update JSON: {e}\nReceived text: {update_text[:500]}")
        except Exception as e:
            raise Exception(f"Error creating update: {e}")

    def _apply_plan_update(self, update: PlanUpdate):
        """Applies an update to the current plan"""
        if not self.current_plan:
            return

        # Remove tasks marked for deletion
        self.current_plan.tasks = [
            task for task in self.current_plan.tasks
            if task.id not in update.removed_task_ids
        ]

        # Update modified tasks
        for modified_task in update.modified_tasks:
            for i, task in enumerate(self.current_plan.tasks):
                if task.id == modified_task.id:
                    self.current_plan.tasks[i] = modified_task
                    break

        # Add new tasks
        if update.new_tasks:
            # Find the current maximum ID
            max_id = max([task.id for task in self.current_plan.tasks], default=0)
            for i, new_task in enumerate(update.new_tasks):
                # Reassign IDs to avoid conflicts
                new_task.id = max_id + i + 1
            self.current_plan.tasks.extend(update.new_tasks)

    def get_next_task(self) -> Optional[Task]:
        """Gets the next pending task that can be executed"""
        if not self.current_plan:
            return None

        for task in self.current_plan.tasks:
            if task.status != "pending":
                continue

            # Verify that all dependencies are completed
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
        """Updates the status of a task"""
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
        """Gets a summary of the current plan"""
        if not self.current_plan:
            return "No active plan"

        completed = sum(1 for t in self.current_plan.tasks if t.status == "completed")
        failed = sum(1 for t in self.current_plan.tasks if t.status == "failed")
        in_progress = sum(1 for t in self.current_plan.tasks if t.status == "in_progress")
        pending = sum(1 for t in self.current_plan.tasks if t.status == "pending")

        summary = f"""=== EXECUTION PLAN ===
Goal: {self.current_plan.goal}
Complexity: {self.current_plan.estimated_complexity}
Reasoning: {self.current_plan.reasoning}

Progress:
  ✓ Completed: {completed}
  ⚡ In progress: {in_progress}
  ○ Pending: {pending}
  ✗ Failed: {failed}
  Total: {len(self.current_plan.tasks)}

Tasks:
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
        """Checks if all tasks in the plan are completed"""
        if not self.current_plan:
            return True

        return all(
            task.status in ["completed", "failed"]
            for task in self.current_plan.tasks
        )

    def get_plan_json(self) -> str:
        """Gets the plan in JSON format"""
        if not self.current_plan:
            return "{}"
        return self.current_plan.model_dump_json(indent=2, exclude_none=True)
