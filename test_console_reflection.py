"""
Quick test to verify thoughts are shown in console before tool calls
"""
import asyncio
import os
from pathlib import Path

# Setup path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool

MODEL_INFO = {
    "vision": False,
    "function_calling": True,
    "json_output": True,
    "structured_output": False,
    "family": "unknown",
}

def list_files(directory: str = ".") -> str:
    """List files in a directory"""
    try:
        files = os.listdir(directory)
        return f"Files in {directory}: {', '.join(files[:5])}"
    except Exception as e:
        return f"Error: {str(e)}"

async def main():
    # Create client
    api_key = os.getenv("DAVEAGENT_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("DAVEAGENT_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DAVEAGENT_BASE_MODEL", "deepseek-chat")

    client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        model_info=MODEL_INFO,
    )

    # Create agent with tools
    tools = [FunctionTool(list_files, description="List files in directory")]

    agent = AssistantAgent(
        name="Explorer",
        system_message="You explore directories. Always explain your thinking BEFORE using tools.",
        model_client=client,
        tools=tools,
        reflect_on_tool_use=True,  # Enable thought reflection before tool calls
    )

    team = RoundRobinGroupChat([agent], termination_condition=MaxMessageTermination(2))

    print("=" * 80)
    print("Testing if thoughts appear in console BEFORE tool calls")
    print("=" * 80)

    # Run and capture events
    async for message in team.run_stream(task="List the files in the test directory"):
        msg_type = type(message).__name__

        if msg_type == "ThoughtEvent":
            print(f"\n[THOUGHT] DETECTED: {message.content}")
        elif msg_type == "ToolCallRequestEvent":
            print(f"\n[TOOL CALL] DETECTED: {message.content}")
        elif msg_type == "ToolCallExecutionEvent":
            print(f"\n[TOOL RESULT] DETECTED")

    print("\n" + "=" * 80)
    print("If you saw '[THOUGHT]' BEFORE '[TOOL CALL]', it's working!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
