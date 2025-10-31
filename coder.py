from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, Any, List, Optional, Tuple
import queue
import json
from autogen_agentchat.conditions import TextMentionTermination,MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
import os
from autogen_core import CancellationToken
import glob
import re
from pathlib import Path
from datetime import datetime
import threading
import time


from httpcore import stream
from tools import (
    read_file, write_file, list_dir, run_terminal_cmd, codebase_search,
    grep_search, file_search, delete_file, diff_history,edit_file
)
from autogen_agentchat.messages import TextMessage
from prompt import AGENT_SYSTEM_PROMPT


import asyncio

# Funciones wrapper para los agentes
def execute_tool(tool_name: str, **kwargs) -> str:
    """Ejecuta una herramienta por nombre con los parámetros dados"""
    tools_map = {
        "read_file": read_file,
        "write_file": write_file,
        "list_dir": list_dir,
        "run_terminal_cmd": run_terminal_cmd,
        "codebase_search": codebase_search,
        "grep_search": grep_search,
        "file_search": file_search,
        "delete_file": delete_file,
        "diff_history": diff_history,
        "edit_file": edit_file
    }
    
    if tool_name in tools_map:
        return tools_map[tool_name](**kwargs)
    else:
        return f"Error: Tool '{tool_name}' not found"



model_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key="sk-8cb1f4fc5bd74bd3a83f31204b942d60",
            model_capabilities={
                "vision": True,
                "function_calling": True,
                "json_output": True,
            },
        )

coder_tools = [
    read_file, write_file, list_dir, run_terminal_cmd,edit_file,
    codebase_search, grep_search, file_search, delete_file, diff_history
]

AGENT_PLAN_PROMPT = """ USER INPUT: """


coder_agent =AssistantAgent(
    name="Coder",
    system_message=AGENT_SYSTEM_PROMPT,
     model_client=model_client,
    tools=coder_tools,            
)


termination = TextMentionTermination("TERMINATE")| MaxMessageTermination(10)


# Create the team.
team = RoundRobinGroupChat([coder_agent], termination_condition=termination)

async def test_coder_agent():
    """
    Función principal para enviar una tarea de prueba al Coder y ver su respuesta.
    """
    print("🚀 Iniciando prueba del Agente Codificador...")
    print("=" * 50)

    # --- Tarea de Prueba ---
    # Define aquí la tarea específica que quieres que el agente realice.
    # Puedes cambiar esta descripción para probar diferentes capacidades.
    task_description = AGENT_PLAN_PROMPT
    print(f"📝 Tarea para el agente:\n{task_description}\n")
    
    # Enviamos el mensaje al agente y esperamos su respuesta.
    # `on_messages` manejará el diálogo interno del agente, incluyendo el uso de herramientas.
    print("🤖 El agente está trabajando en la tarea... (esto puede tardar un momento)")
    final_response = team.run_stream(task=task_description)
    await Console(final_response)
    await model_client.close()
    print("\n" + "=" * 50)
    print("✅ Prueba completada.")
    
    print("Respuesta final del agente:")
    print(final_response)

# --- Punto de Entrada del Script ---

if __name__ == "__main__":
    # `asyncio.run()` es necesario para ejecutar la función asíncrona `test_coder_agent`.
    asyncio.run(test_coder_agent())
