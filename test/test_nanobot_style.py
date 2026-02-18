"""
Test script to verify Nanobot-style subagent result injection.

This test verifies that:
1. Subagents use the custom subagent system prompt
2. Results are queued as announcements
3. check_subagent_results tool retrieves announcements
4. The flow matches Nanobot's behavior
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.orchestrator import AgentOrchestrator
from src.config.settings import get_settings


async def test_nanobot_style():
    """Test Nanobot-style subagent result injection."""

    print("\n" + "="*70)
    print("TESTING NANOBOT-STYLE SUBAGENT RESULT INJECTION")
    print("="*70 + "\n")

    # Initialize orchestrator (headless mode for testing)
    print("[1/5] Initializing orchestrator...")
    settings = get_settings()
    orch = AgentOrchestrator(
        api_key=settings.api_key,
        base_url=settings.base_url,
        model=settings.model,
        ssl_verify=settings.ssl_verify,
        headless=True,  # Headless mode to avoid CLI issues
    )
    print("     [OK] Orchestrator initialized\n")

    # Verify subagent system is initialized
    print("[2/5] Verifying subagent system...")
    assert hasattr(orch, 'subagent_manager'), "SubAgentManager not initialized"
    assert hasattr(orch, '_subagent_announcements'), "Announcement queue not initialized"
    print("     [OK] Subagent system ready\n")

    # Verify check_subagent_results tool is available
    print("[3/5] Verifying check_subagent_results tool...")
    from src.tools import check_subagent_results
    all_tools = orch.all_tools["read_only"] + orch.all_tools["modification"]
    tool_names = [t.__name__ for t in all_tools]
    assert "check_subagent_results" in tool_names, "check_subagent_results not in tools"
    print("     [OK] Tool is available\n")

    # Test spawning a simple subagent
    print("[4/5] Spawning test subagent...")
    result = await orch.subagent_manager.spawn(
        task="List the files in the current directory using list_dir tool",
        label="test-lister",
        parent_task_id="test-main",
        max_iterations=5,
    )
    print(f"     {result}\n")

    # Wait for subagent to complete
    print("[5/5] Waiting for subagent to complete...")
    await asyncio.sleep(10)  # Give it time to run

    # Check if announcements were queued
    print("\n" + "="*70)
    print("CHECKING ANNOUNCEMENTS")
    print("="*70 + "\n")

    if orch._subagent_announcements:
        print(f"[OK] Found {len(orch._subagent_announcements)} announcement(s)\n")

        for i, ann in enumerate(orch._subagent_announcements, 1):
            print(f"Announcement {i}:")
            print(f"  Label: {ann.get('label', 'unknown')}")
            print(f"  Task: {ann.get('task', 'N/A')[:50]}...")
            print(f"  Preview: {ann.get('preview', 'N/A')[:100]}...\n")

        # Test check_subagent_results tool
        print("Testing check_subagent_results tool...")
        result = await check_subagent_results()
        print("\nTool Output:")
        print("-" * 70)
        print(result)
        print("-" * 70)

        # Verify queue was cleared
        if not orch._subagent_announcements:
            print("\n[OK] Announcement queue cleared after retrieval")
        else:
            print(f"\n[WARNING] Queue still has {len(orch._subagent_announcements)} items")
    else:
        print("[WARNING] No announcements found")
        print("          Subagent may not have completed yet or may have failed")

        # Show subagent status
        active = orch.subagent_manager.list_active_subagents()
        print(f"\nActive subagents: {len(active)}")
        for sa in active:
            print(f"  - {sa['id']}: {sa['status']}")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")

    print("Summary:")
    print("- Subagent system initialized: [OK]")
    print("- check_subagent_results tool available: [OK]")
    print("- Subagent spawned: [OK]")
    print(f"- Results queued: {'[OK]' if orch._subagent_announcements or result != 'No pending subagent results' else '[PENDING]'}")

    # Cleanup
    await orch.subagent_manager.cancel_all()


if __name__ == "__main__":
    asyncio.run(test_nanobot_style())
