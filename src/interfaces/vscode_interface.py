"""
VS Code Interface - JSON based communication for the VS Code Extension
"""

import asyncio
import json
import sys
from typing import Any

# We'll just inherit from object/dummy or try to match CLIInterface signature
# Since Python doesn't enforce interfaces strictly, we just need the same methods.


class VSCodeInterface:
    """
    Interface for VS Code integration.
    Instead of printing to console with Rich, it emits JSON objects to stdout.
    Reads input from stdin as JSON when requested.
    """

    def __init__(self):
        self.mentioned_files: list[str] = []
        self.current_mode = "agent"
        # We don't need rich console or prompt session

    def _emit_event(self, event_type: str, data: Any = None):
        """Emit a JSON event to stdout"""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        # Print JSON line and flush to ensure VS Code receives it immediately
        print(json.dumps(message), flush=True)

    def print_banner(self):
        """No banner in VS Code mode"""
        self._emit_event("banner", {"started": True})

    def set_mode(self, mode: str):
        self.current_mode = mode
        self._emit_event("mode_change", {"mode": mode})

    async def get_user_input(self, prompt: str = "") -> str:
        """
        Request user input via JSON event.
        Waits for a JSON object on stdin.
        """
        self._emit_event("request_input", {"prompt": prompt})

        # Run in executor to avoid blocking the loop while reading stdin
        loop = asyncio.get_event_loop()
        line = await loop.run_in_executor(None, sys.stdin.readline)

        if not line:
            return "/exit"

        try:
            # Expecting JSON input from VS Code extension
            # Format: {"input": "user message", "files": ["file1", "file2"]}
            data = json.loads(line)
            user_input = data.get("input", "")

            # Update mentioned files if provided
            if "files" in data:
                # We append or replace? Let's append
                new_files = data.get("files", [])
                for f in new_files:
                    if f not in self.mentioned_files:
                        self.mentioned_files.append(f)

            return user_input.strip()

        except json.JSONDecodeError:
            # Fallback for plain text input (e.g. debugging)
            return line.strip()

    def print_user_message(self, message: str):
        # Echo back (optional, mostly for confirmation)
        self._emit_event("user_message", {"content": message})

    def print_agent_message(self, message: str, agent_name: str = "Agent"):
        self._emit_event("agent_message", {"agent": agent_name, "content": message})

    def print_plan(self, plan_summary: str):
        self._emit_event("plan", {"content": plan_summary})

    def print_task_start(self, task_id: int, task_title: str, task_description: str):
        self._emit_event("task_start", {
            "id": task_id,
            "title": task_title,
            "description": task_description
        })

    def print_task_complete(self, task_id: int, task_title: str, result_summary: str):
        self._emit_event("task_complete", {
            "id": task_id,
            "title": task_title,
            "summary": result_summary
        })

    def print_task_failed(self, task_id: int, task_title: str, error: str):
        self._emit_event("task_failed", {
            "id": task_id,
            "title": task_title,
            "error": error
        })

    def print_plan_update(self, reasoning: str, changes_summary: str):
        self._emit_event("plan_update", {
            "reasoning": reasoning,
            "changes": changes_summary
        })

    def start_thinking(self, message: str | None = None):
        self._emit_event("start_thinking", {"message": message or "Thinking..."})

    def stop_thinking(self, clear: bool = True):
        self._emit_event("stop_thinking", {"clear": clear})

    def print_thinking(self, message: str = "Thinking..."):
        self._emit_event("thought", {"content": message})

    def print_error(self, error: str):
        self._emit_event("error", {"content": error})

    def print_warning(self, warning: str):
        self._emit_event("warning", {"content": warning})

    def print_info(self, info: str, title: str = "Information"):
        self._emit_event("info", {"title": title, "content": info})

    def print_success(self, message: str):
        self._emit_event("success", {"content": message})

    def print_diff(self, diff_text: str):
        self._emit_event("diff", {"content": diff_text})

    def print_task_summary(self, summary: str):
        self._emit_event("summary", {"content": summary})

    def create_progress_table(self, tasks: list[dict]):
        # Just send the raw tasks list
        self._emit_event("progress_table", {"tasks": tasks})

    def print_statistics(self, stats: dict):
        self._emit_event("statistics", {"stats": stats})

    def print_help(self):
        # Just a simple message, help is handled by VS Code UI mostly
        self._emit_event("info", {"content": "Help is available in the VS Code sidebar."})

    def print_goodbye(self):
        self._emit_event("goodbye", {})

    def clear_screen(self):
        # Not applicable but can signal UI clear
        self._emit_event("clear_screen", {})

    def get_mentioned_files(self) -> list[str]:
        return self.mentioned_files.copy()

    def clear_mentioned_files(self):
        self.mentioned_files.clear()

    def print_mentioned_files(self):
        self._emit_event("mentioned_files", {"files": self.mentioned_files})

    def get_mentioned_files_content(self) -> str:
        # Same implementation as CLIInterface basically, but we can reuse the logic
        # Or just import it if it was a static method or helper.
        # For now, duplicate simpler version
        if not self.mentioned_files:
            return ""

        content_parts = []
        content_parts.append("📎 MENTIONED FILES CONTEXT (High Priority):\n")

        for file_path in self.mentioned_files:
            try:
                # Basic read
                import os
                if os.path.exists(file_path):
                    with open(file_path, encoding="utf-8") as f:
                        file_content = f.read()

                    content_parts.append(f"\\n{'=' * 60}")
                    content_parts.append(f"FILE: {file_path}")
                    content_parts.append(f"{'=' * 60}\\n")
                    content_parts.append(file_content)
                    content_parts.append(f"\\n{'=' * 60}\\n")
            except Exception:
                pass

        return "\\n".join(content_parts)

    def stop_task_tracking(self):
        """Mock method for when main.py calls this (it's in CLIInterface but not used heavily)"""
        pass

    @property
    def task_panel_active(self):
        return False
