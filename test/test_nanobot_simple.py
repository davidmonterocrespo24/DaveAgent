"""
Simplified test for Nanobot-style integration - just verify the components.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all components can be imported."""
    print("\n" + "=" * 70)
    print("TEST 1: Import all components")
    print("=" * 70)

    try:
        from src.tools import check_subagent_results

        print("[OK] check_subagent_results imported")
    except ImportError as e:
        print(f"[FAIL] Could not import check_subagent_results: {e}")
        return False

    try:
        from src.config.prompts import SUBAGENT_SYSTEM_PROMPT

        print("[OK] SUBAGENT_SYSTEM_PROMPT imported")
    except ImportError as e:
        print(f"[FAIL] Could not import SUBAGENT_SYSTEM_PROMPT: {e}")
        return False

    try:
        from src.subagents import SubagentEventBus, SubAgentManager

        print("[OK] SubagentEventBus and SubAgentManager imported")
    except ImportError as e:
        print(f"[FAIL] Could not import subagent components: {e}")
        return False

    return True


def test_system_prompt():
    """Test that subagent system prompt works."""
    print("\n" + "=" * 70)
    print("TEST 2: Generate subagent system prompt")
    print("=" * 70)

    try:
        from src.config.prompts import SUBAGENT_SYSTEM_PROMPT

        task = "Analyze all Python files in src/"
        workspace = str(Path.cwd())

        prompt = SUBAGENT_SYSTEM_PROMPT(task=task, workspace_path=workspace)

        # Verify key elements
        assert "subagent" in prompt.lower(), "Prompt doesn't mention subagent"
        assert task in prompt, "Prompt doesn't include task"
        assert workspace in prompt, "Prompt doesn't include workspace"
        assert "cannot do" in prompt.lower() or "cannot" in prompt.lower(), (
            "Prompt doesn't have restrictions"
        )

        print(f"[OK] Generated prompt ({len(prompt)} chars)")
        print(f"     Contains task: {task in prompt}")
        print(f"     Contains workspace: {workspace in prompt}")
        print(f"     Has restrictions: {'Cannot' in prompt}")

        return True
    except Exception as e:
        print(f"[FAIL] Error generating prompt: {e}")
        return False


def test_tool_registration():
    """Test that check_subagent_results is in tools list."""
    print("\n" + "=" * 70)
    print("TEST 3: Verify tool registration")
    print("=" * 70)

    try:
        from src.config.orchestrator import AgentOrchestrator
        from src.config.settings import get_settings
        from src.tools import check_subagent_results

        settings = get_settings()
        orch = AgentOrchestrator(
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=settings.model,
            ssl_verify=settings.ssl_verify,
            headless=True,
        )

        # Check tool is in read_only tools
        all_tools = orch.all_tools["read_only"] + orch.all_tools["modification"]
        tool_names = [t.__name__ for t in all_tools]

        assert "check_subagent_results" in tool_names, "Tool not found in tools list"
        assert "spawn_subagent" in tool_names, "spawn_subagent not found"

        print(f"[OK] Found {len(tool_names)} tools total")
        print("     check_subagent_results: present")
        print("     spawn_subagent: present")

        # Check announcement queue
        assert hasattr(orch, "_subagent_announcements"), "No announcement queue"
        print("     Announcement queue: initialized")

        return True
    except Exception as e:
        print(f"[FAIL] Error checking tool registration: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_announcement_queue():
    """Test the announcement queueing system."""
    print("\n" + "=" * 70)
    print("TEST 4: Test announcement queue")
    print("=" * 70)

    try:
        import asyncio
        import sys

        from src.config.orchestrator import AgentOrchestrator
        from src.config.settings import get_settings
        from src.tools import check_subagent_results

        settings = get_settings()
        orch = AgentOrchestrator(
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=settings.model,
            ssl_verify=settings.ssl_verify,
            headless=True,
        )

        # Manually add a test announcement
        orch._subagent_announcements.append(
            {
                "label": "test-task",
                "task": "Test task description",
                "result": "Test result output",
                "preview": "Test result...",
                "announcement": "[Background Task Completed: test-task]\n\nTask: Test\n\nResult: Test result",
            }
        )

        print("[OK] Added test announcement")
        print(f"     Queue size: {len(orch._subagent_announcements)}")

        # Initialize check tool
        check_module = sys.modules["src.tools.check_subagent_results"]
        check_module.set_orchestrator(orch)

        # Call check_subagent_results
        async def test():
            result = await check_subagent_results()
            return result

        result = asyncio.run(test())

        assert "Background Task Completed" in result, "Result doesn't contain announcement"
        assert len(orch._subagent_announcements) == 0, "Queue not cleared"

        print("[OK] Retrieved announcement")
        print(f"     Queue cleared: {len(orch._subagent_announcements) == 0}")
        print(f"     Result preview: {result[:100]}...")

        return True
    except Exception as e:
        print(f"[FAIL] Error testing announcement queue: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("NANOBOT-STYLE INTEGRATION - COMPONENT TESTS")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("System Prompt", test_system_prompt()))
    results.append(("Tool Registration", test_tool_registration()))
    results.append(("Announcement Queue", test_announcement_queue()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All components working correctly!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
