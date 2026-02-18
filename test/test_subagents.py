"""
Quick test script to verify the subagent system works correctly.

This script tests:
1. Event bus functionality
2. Tool filtering
3. SubAgent manager initialization
"""

import asyncio
import sys
import os

# Windows console compatibility - use ASCII characters
CHECK = "[OK]"
CROSS = "[FAIL]"

# Add project root to path
sys.path.insert(0, os.getcwd())


async def test_event_bus():
    """Test the event bus"""
    from src.subagents import SubagentEventBus, SubagentEvent

    print("Testing Event Bus...")
    bus = SubagentEventBus()

    # Test event subscription
    events_received = []

    async def on_event(event):
        events_received.append(event)

    bus.subscribe("test_event", on_event)

    # Publish event
    await bus.publish(SubagentEvent(
        subagent_id="test123",
        parent_task_id="main",
        event_type="test_event",
        content={"message": "Hello from test"}
    ))

    assert len(events_received) == 1, "Should receive 1 event"
    assert events_received[0].subagent_id == "test123"
    print(f"{CHECK} Event bus works correctly")


def test_tool_filtering():
    """Test tool filtering"""
    from src.subagents import create_tool_subset, get_tool_names

    print("\nTesting Tool Filtering...")

    # Mock tools
    async def tool_a():
        pass

    async def tool_b():
        pass

    async def spawn_subagent():
        pass

    tool_a.__name__ = "tool_a"
    tool_b.__name__ = "tool_b"
    spawn_subagent.__name__ = "spawn_subagent"

    all_tools = [tool_a, tool_b, spawn_subagent]

    # Filter out spawn_subagent
    filtered = create_tool_subset(all_tools, exclude_names=["spawn_subagent"])

    assert len(filtered) == 2, "Should have 2 tools after filtering"
    assert get_tool_names(filtered) == ["tool_a", "tool_b"]
    print(f"{CHECK} Tool filtering works correctly")


async def test_subagent_manager():
    """Test SubAgent manager initialization"""
    from src.subagents import SubagentEventBus, SubAgentManager

    print("\nTesting SubAgent Manager...")

    bus = SubagentEventBus()

    # Mock orchestrator factory
    def mock_factory(tools, max_iterations, mode):
        return type('MockOrchestrator', (), {
            'run_task': lambda self, task: asyncio.sleep(0.1)
        })()

    manager = SubAgentManager(
        event_bus=bus,
        orchestrator_factory=mock_factory,
        base_tools=[]
    )

    assert manager is not None
    assert len(manager.list_active_subagents()) == 0
    print(f"{CHECK} SubAgent manager initializes correctly")


async def test_spawn_tool():
    """Test spawn tool initialization"""
    from src.tools.spawn_subagent import set_subagent_manager, spawn_subagent
    from src.subagents import SubagentEventBus, SubAgentManager

    print("\nTesting Spawn Tool...")

    # Setup
    bus = SubagentEventBus()

    def mock_factory(tools, max_iterations, mode):
        class MockOrchestrator:
            async def run_task(self, task):
                await asyncio.sleep(0.05)
                return f"Completed: {task}"
        return MockOrchestrator()

    manager = SubAgentManager(
        event_bus=bus,
        orchestrator_factory=mock_factory,
        base_tools=[]
    )

    set_subagent_manager(manager, "test")

    # Test spawn
    result = await spawn_subagent(
        task="Test task",
        label="test_agent"
    )

    assert "spawned" in result.lower()
    assert "test_agent" in result
    print(f"{CHECK} Spawn tool works correctly")

    # Wait for subagent to complete
    await asyncio.sleep(0.2)

    # Check events
    events = bus.get_events_for_subagent(result.split("ID: ")[1].rstrip(")"))
    assert len(events) >= 2  # spawned + completed
    print(f"{CHECK} Subagent execution and events work correctly")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("SUBAGENT SYSTEM TEST SUITE")
    print("=" * 60)

    try:
        # Run tests
        await test_event_bus()
        test_tool_filtering()
        await test_subagent_manager()
        await test_spawn_tool()

        print("\n" + "=" * 60)
        print(f"{CHECK} ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe subagent system is ready to use.")
        print("\nNext steps:")
        print("1. Start the agent: python -m src.main")
        print("2. Try spawning subagents with the spawn_subagent tool")
        print("3. Monitor parallel execution via event notifications")
        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"{CROSS} TEST FAILED!")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
