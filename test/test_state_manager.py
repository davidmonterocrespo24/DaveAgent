"""
Test: StateManager save/load with a basic RoundRobinGroupChat team.

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
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.managers.state_manager import StateManager

MODEL_INFO = {
    "vision": False,
    "function_calling": True,
    "json_output": True,
    "structured_output": False,
    "family": "unknown",
}


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
    client = make_client()
    agent1 = AssistantAgent(
        name="Poet",
        system_message="You are a poet. Write short beautiful poems when asked.",
        model_client=client,
    )
    agent2 = AssistantAgent(
        name="Critic",
        system_message="You are a literary critic. Comment briefly on the previous poem.",
        model_client=client,
    )
    team = RoundRobinGroupChat(
        [agent1, agent2],
        termination_condition=MaxMessageTermination(max_messages=4),
    )
    return team, agent1, agent2


async def main():
    state_manager = StateManager()
    state_file = Path(".daveagent") / "agent_state.json"

    print("=" * 60)
    print("PHASE 1: Run team and save state")
    print("=" * 60)

    team, _, _ = make_team()
    await Console(team.run_stream(task="Write a 3-line poem about the ocean."))

    # Save via StateManager
    saved_path = await state_manager.save_team_state(team)
    print(f"\n✅ State saved to: {saved_path}")

    # Show what was saved
    with open(saved_path) as f:
        saved = json.load(f)
    print(f"   Keys in saved state: {list(saved.keys())}")

    print("\n" + "=" * 60)
    print("PHASE 2: Create NEW team (simulating fresh restart) and ask follow-up WITHOUT loading state")
    print("=" * 60)

    fresh_team, _, _ = make_team()
    await Console(fresh_team.run_stream(task="What was the last line of the poem you just wrote?"))

    print("\n" + "=" * 60)
    print("PHASE 3: Create another NEW team, LOAD state, ask the same follow-up")
    print("=" * 60)

    restored_team, _, _ = make_team()
    loaded = await state_manager.load_team_state(restored_team)
    print(f"   State loaded: {loaded}")

    await Console(restored_team.run_stream(task="What was the last line of the poem you just wrote?"))

    print("\n" + "=" * 60)
    print("PHASE 4: Verify session metadata persistence")
    print("=" * 60)

    session_id = state_manager.start_session(title="Ocean Poem Test")
    await state_manager.save_to_disk(session_id)
    print(f"   Session saved: {session_id}")

    sessions = state_manager.list_sessions()
    print(f"   Sessions found: {len(sessions)}")
    for s in sessions:
        print(f"   - [{s['session_id']}] {s['title']} (saved: {s.get('saved_at', '?')})")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
