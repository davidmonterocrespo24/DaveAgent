r"""
Test: StateManager save/load with tool-using agents to verify tool reflection capture.

This test demonstrates:
1. How agents use tools (read_file, list_dir)
2. How tool calls and reflections are saved in state
3. How to analyze saved state to extract tool usage patterns

Usage:
    cd e:\AI\CodeAgent
    python -m test.test_state_manager
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Load .env (prefer root .env which has the valid key)
project_root = Path(__file__).resolve().parent.parent
legacy_env = project_root / ".env"
daveagent_env = project_root / ".daveagent" / ".env"
if legacy_env.exists():
    load_dotenv(legacy_env)
if daveagent_env.exists():
    load_dotenv(daveagent_env, override=False)  # don't override already-loaded values

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.managers.state_manager import StateManager

MODEL_INFO = {
    "vision": False,
    "function_calling": True,
    "json_output": True,
    "structured_output": False,
    "family": "unknown",
}


# =========================================================================
# Simple Tools for Testing
# =========================================================================


def read_file_tool(file_path: str) -> str:
    """
    Read the contents of a file.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        return f"File '{file_path}' ({len(content)} chars):\n{content[:500]}..."
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_directory_tool(directory: str = ".") -> str:
    """
    List files and directories in a given path.

    Args:
        directory: Directory path to list (defaults to current directory)

    Returns:
        Formatted list of files and directories
    """
    try:
        items = os.listdir(directory)
        files = [f for f in items if os.path.isfile(os.path.join(directory, f))]
        dirs = [d for d in items if os.path.isdir(os.path.join(directory, d))]

        result = f"Directory '{directory}' contents:\n"
        result += f"  📁 Directories ({len(dirs)}): {', '.join(dirs[:10])}\n"
        result += f"  📄 Files ({len(files)}): {', '.join(files[:10])}"
        return result
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def get_file_info_tool(file_path: str) -> str:
    """
    Get metadata about a file (size, type, etc).

    Args:
        file_path: Path to the file

    Returns:
        File metadata as formatted string
    """
    try:
        if not os.path.exists(file_path):
            return f"File '{file_path}' does not exist"

        stats = os.stat(file_path)
        size = stats.st_size
        is_file = os.path.isfile(file_path)

        return f"File info for '{file_path}':\n  Type: {'File' if is_file else 'Directory'}\n  Size: {size} bytes"
    except Exception as e:
        return f"Error getting file info: {str(e)}"


def make_client() -> OpenAIChatCompletionClient:
    api_key = os.getenv("DAVEAGENT_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("DAVEAGENT_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DAVEAGENT_BASE_MODEL", "deepseek-chat")
    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        model_info=MODEL_INFO,
    )


def make_team() -> tuple[RoundRobinGroupChat, AssistantAgent, AssistantAgent]:
    """Create a team with tool-using agents"""
    client = make_client()

    # Create tools
    tools = [
        FunctionTool(read_file_tool, description="Read file contents"),
        FunctionTool(list_directory_tool, description="List directory contents"),
        FunctionTool(get_file_info_tool, description="Get file metadata"),
    ]

    # Agent 1: File Explorer - uses tools to explore files
    agent1 = AssistantAgent(
        name="FileExplorer",
        system_message=(
            "You are a file system explorer. When asked about files or directories, "
            "use the available tools to investigate and provide detailed information. "
            "Always explain what you're going to do BEFORE using a tool."
        ),
        model_client=client,
        tools=tools,
    )

    # Agent 2: Analyzer - analyzes results from agent1
    agent2 = AssistantAgent(
        name="Analyzer",
        system_message=(
            "You are a code analyzer. Review the file exploration results and provide "
            "insights about the project structure, file types, or suggest next steps."
        ),
        model_client=client,
    )

    team = RoundRobinGroupChat(
        [agent1, agent2],
        termination_condition=MaxMessageTermination(max_messages=6),
    )
    return team, agent1, agent2


def analyze_tool_reflections(state_data: dict) -> None:
    """
    Analyze and display tool usage reflections from saved state.

    This function inspects the saved state to find:
    1. Tool calls made by agents
    2. Thoughts/reasoning before tool calls (if available)
    3. Tool execution results
    """
    print("\n" + "=" * 80)
    print("🔍 TOOL REFLECTION ANALYSIS")
    print("=" * 80)

    agent_states = state_data.get("agent_states", {})

    total_tools_called = 0
    tools_with_reflection = 0
    tools_without_reflection = 0

    for agent_key, agent_data in agent_states.items():
        # Extract agent name from the key (format: "AgentName/uuid")
        agent_name = agent_key.split("/")[0]

        agent_state = agent_data.get("state", {})
        if agent_state.get("type") == "ChatAgentContainerState":
            agent_state = agent_state.get("agent_state", {})

        llm_messages = agent_state.get("llm_messages", [])

        print(f"\n📦 Agent: {agent_name}")
        print("-" * 80)

        for i, msg in enumerate(llm_messages):
            msg_type = msg.get("type")

            # Look for AssistantMessage with tool calls
            if msg_type == "AssistantMessage":
                content = msg.get("content")
                thought = msg.get("thought")

                # Check if this message contains tool calls
                if isinstance(content, list) and len(content) > 0:
                    for tool_call in content:
                        if isinstance(tool_call, dict) and "name" in tool_call:
                            total_tools_called += 1
                            tool_name = tool_call.get("name")
                            tool_args = tool_call.get("arguments", {})

                            print(f"\n  🔧 Tool Call #{total_tools_called}: {tool_name}")
                            print(f"     Arguments: {tool_args}")

                            # Check for reflection/thought
                            if thought:
                                tools_with_reflection += 1
                                print(f"     💭 Thought/Reflection: {thought}")
                            else:
                                tools_without_reflection += 1
                                print("     ⚠️  No thought/reflection captured")

                            # Look for the result in next messages
                            if i + 1 < len(llm_messages):
                                next_msg = llm_messages[i + 1]
                                if next_msg.get("type") == "FunctionExecutionResultMessage":
                                    results = next_msg.get("content", [])
                                    for result in results:
                                        if isinstance(result, dict):
                                            result_content = result.get("content", "")
                                            print(f"     ✅ Result: {result_content[:200]}...")

    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"  Total tools called: {total_tools_called}")
    print(f"  Tools WITH reflection/thought: {tools_with_reflection}")
    print(f"  Tools WITHOUT reflection/thought: {tools_without_reflection}")

    if total_tools_called > 0:
        percentage = (tools_with_reflection / total_tools_called) * 100
        print(f"  Reflection capture rate: {percentage:.1f}%")

    print("=" * 80)


async def main():
    state_manager = StateManager()

    print("=" * 80)
    print("PHASE 1: Run team with TOOL USAGE and save state")
    print("=" * 80)

    team, agent1, _ = make_team()

    # Task that will trigger tool usage
    task = "Explore the test directory and tell me what files are there. Then read the README.md file if it exists."

    await Console(team.run_stream(task=task))

    # Save state via StateManager
    session_id = state_manager.start_session(title="Tool Usage Test")
    await state_manager.save_agent_state(
        "FileExplorer", agent1, metadata={"test": "tool_reflection"}
    )
    await state_manager.save_team_state("main_team", team, metadata={"task": task})

    saved_path = await state_manager.save_to_disk(session_id)
    print(f"\n✅ State saved to: {saved_path}")

    # Load and analyze the saved state
    with open(saved_path) as f:
        saved_state = json.load(f)

    print("\n📋 Saved state structure:")
    print(f"   - session_id: {saved_state.get('session_id')}")
    print(f"   - agent_states: {list(saved_state.get('agent_states', {}).keys())}")
    print(f"   - team_states: {list(saved_state.get('team_states', {}).keys())}")

    # Analyze tool reflections using OLD method (for comparison)
    analyze_tool_reflections(saved_state)

    # NEW: Use StateManager's built-in tool reflection analysis
    print("\n" + "=" * 80)
    print("📊 NEW: StateManager Tool Reflection Analysis")
    print("=" * 80)

    reflections = state_manager.extract_tool_reflections(session_id)
    print(f"\n✅ Extracted {len(reflections)} tool reflections")

    for i, ref in enumerate(reflections[:5], 1):  # Show first 5
        print(f"\n{i}. Agent: {ref['agent']} | Tool: {ref['tool_name']}")
        print(f"   💭 Thought: {ref['thought'][:100] if ref['thought'] else 'None'}...")
        print(f"   ✅ Result: {ref['result'][:100] if ref['result'] else 'None'}...")
        print(f"   ⚠️  Error: {ref['is_error']}")

    # Get statistics
    stats = state_manager.get_tool_usage_stats(session_id)
    print("\n" + "=" * 80)
    print("📈 Tool Usage Statistics")
    print("=" * 80)
    print(f"  Total tools called: {stats['total_tools_called']}")
    print(f"  Tools WITH reflection: {stats['tools_with_reflection']}")
    print(f"  Tools WITHOUT reflection: {stats['tools_without_reflection']}")
    print(f"  Reflection rate: {stats['reflection_rate']:.1f}%")
    print(f"  Error rate: {stats['error_rate']:.1f}%")
    print(f"  Agents using tools: {stats['agents_using_tools']}")
    print("\n  Tool Frequency:")
    for tool, count in stats["tool_frequency"].items():
        print(f"    - {tool}: {count} calls")

    # Save reflection report
    report_path = state_manager.save_tool_reflection_report(session_id)
    print(f"\n📄 Detailed report saved to: {report_path}")

    print("\n" + "=" * 80)
    print("PHASE 2: Create NEW team, LOAD state, and continue conversation")
    print("=" * 80)

    # Create fresh team
    new_team, new_agent1, _ = make_team()

    # Load state
    await state_manager.load_from_disk(session_id)
    await state_manager.load_agent_state("FileExplorer", new_agent1)
    await state_manager.load_team_state("main_team", new_team)

    print("✅ State loaded successfully")

    # Ask follow-up question that requires context from previous tool usage
    follow_up_task = (
        "Based on what you found earlier, what types of files are in the test directory?"
    )
    await Console(new_team.run_stream(task=follow_up_task))

    print("\n" + "=" * 80)
    print("PHASE 3: Save final state and re-analyze")
    print("=" * 80)

    await state_manager.save_agent_state("FileExplorer", new_agent1)
    await state_manager.save_team_state("main_team", new_team)
    final_path = await state_manager.save_to_disk(session_id)

    with open(final_path) as f:
        final_state = json.load(f)

    analyze_tool_reflections(final_state)

    # Final statistics
    print("\n" + "=" * 80)
    print("📊 FINAL Tool Usage Statistics")
    print("=" * 80)

    final_stats = state_manager.get_tool_usage_stats(session_id)
    print(f"  Total tools called: {final_stats['total_tools_called']}")
    print(f"  Reflection rate: {final_stats['reflection_rate']:.1f}%")
    print(f"  Error rate: {final_stats['error_rate']:.1f}%")

    # Save final report
    final_report_path = state_manager.save_tool_reflection_report(session_id)
    print(f"\n📄 Final detailed report: {final_report_path}")

    print("\n✅ All tests completed!")
    print(f"\n💾 Final state saved to: {final_path}")


if __name__ == "__main__":
    asyncio.run(main())
