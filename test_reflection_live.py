"""
Test to verify ThoughtEvent is generated in the actual orchestrator
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

async def main():
    from src.config.orchestrator import AgentOrchestrator

    print("=" * 80)
    print("Testing ThoughtEvent in real orchestrator")
    print("=" * 80)

    orchestrator = AgentOrchestrator()
    # The orchestrator starts in "agent" mode by default

    # Simple task that will trigger a tool call
    task = "List files in the current directory"

    print(f"\nTask: {task}\n")

    thought_count = 0
    tool_call_count = 0

    async for message in orchestrator.team.run_stream(task=task):
        msg_type = type(message).__name__

        if msg_type == "ThoughtEvent":
            thought_count += 1
            print(f"\n✅ [THOUGHT #{thought_count}] {message.content}")
        elif msg_type == "ToolCallRequestEvent":
            tool_call_count += 1
            print(f"\n🔧 [TOOL CALL #{tool_call_count}] {message.content}")

    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  - Thoughts detected: {thought_count}")
    print(f"  - Tool calls detected: {tool_call_count}")

    if thought_count > 0:
        print("✅ SUCCESS: ThoughtEvent is working!")
    else:
        print("❌ PROBLEM: No ThoughtEvent detected")
        print("   The agent is not generating thoughts before tool calls")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
