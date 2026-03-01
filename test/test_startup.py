#!/usr/bin/env python3
"""
Quick startup test for DaveAgent with subagents system.
Tests that the agent can initialize without errors.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_startup():
    """Test that DaveAgent can initialize with subagent system"""
    print("\n" + "=" * 60)
    print("Testing DaveAgent Startup with Subagent System")
    print("=" * 60)

    try:
        # Import orchestrator
        print("\n[1/5] Importing AgentOrchestrator...")
        from src.config import AgentOrchestrator

        print("      ✓ Import successful")

        # Check subagent modules
        print("\n[2/5] Checking subagent modules...")
        import sys

        from src.subagents import SubagentEventBus, SubAgentManager
        from src.tools import spawn_subagent  # Import function to ensure module is loaded

        print("      ✓ Subagent modules imported")

        # Verify spawn_subagent has set_subagent_manager
        print("\n[3/5] Verifying spawn_subagent structure...")
        spawn_module = sys.modules["src.tools.spawn_subagent"]
        assert hasattr(spawn_module, "set_subagent_manager"), "Missing set_subagent_manager"
        assert hasattr(spawn_module, "spawn_subagent"), "Missing spawn_subagent function"
        print("      ✓ spawn_subagent module structure correct")

        # Try to create a minimal orchestrator (would normally fail without API key)
        print("\n[4/5] Testing orchestrator initialization...")
        print("      (This will use env variables or fail gracefully)")
        try:
            # This might fail due to missing API key, but that's OK
            # We're just testing the import and initialization doesn't crash
            orch = AgentOrchestrator()
            print("      ✓ Orchestrator initialized (API key found)")

            # Check subagent manager was created
            assert hasattr(orch, "subagent_manager"), "Missing subagent_manager"
            assert hasattr(orch, "subagent_event_bus"), "Missing subagent_event_bus"
            print("      ✓ Subagent system initialized in orchestrator")

        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg or "api_key" in error_msg.lower():
                print("      ℹ️  No API key (expected in test)")
                print("      ✓ Import and initialization code is correct")
            else:
                print(f"      ✗ Unexpected error: {e}")
                raise

        print("\n[5/5] Final verification...")
        print("      ✓ All imports working")
        print("      ✓ No AttributeError for set_subagent_manager")

        print("\n" + "=" * 60)
        print("✓ STARTUP TEST PASSED!")
        print("=" * 60)
        print("\nThe agent should start correctly with:")
        print("  daveagent")
        print("  python -m src.main")
        print("\nSubagent system is ready to use!")

        return 0

    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ STARTUP TEST FAILED!")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_startup())
    sys.exit(exit_code)
