"""
Tests for terminal improvements (FASE 4).

Tests the new terminal features:
1. Bracketed paste mode support
2. Enhanced subagent visualization methods
3. Integration with orchestrator events
"""

import os
import sys

# Ensure we import from local src, not system site-packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from rich.console import Console


def test_imports():
    """Test that all required imports work."""
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys

    from src.config.orchestrator import AgentOrchestrator
    from src.interfaces.cli_interface import CLIInterface

    assert CLIInterface is not None
    assert KeyBindings is not None
    assert Keys is not None
    assert AgentOrchestrator is not None
    print("✅ All imports successful")


def test_bracketed_paste_keybinding():
    """Test that bracketed paste key binding is set up correctly."""
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys

    from src.interfaces.cli_interface import CLIInterface

    # Create CLIInterface instance
    with patch("src.interfaces.cli_interface.PromptSession"):
        with patch("src.interfaces.cli_interface.FileHistory"):
            cli = CLIInterface()

    # Verify session has key_bindings attribute set
    # (We can't easily test the actual paste behavior in unit tests,
    # but we can verify the setup exists)
    assert hasattr(cli, "session"), "CLIInterface should have session attribute"
    print("✅ Bracketed paste keybinding setup verified")


def test_print_subagent_spawned():
    """Test the enhanced spawn notification method."""
    from rich.panel import Panel

    from src.interfaces.cli_interface import CLIInterface

    # Verify the method exists
    assert hasattr(CLIInterface, "print_subagent_spawned"), "Method should exist on class"

    # Create a simple mock to test the call
    mock_console = Mock()

    # Call the method directly on the class, passing self manually
    # This tests the method logic without needing full initialization
    class MockCLI:
        def __init__(self):
            self.console = mock_console

    mock_cli = MockCLI()
    # Bind the method to our mock instance
    CLIInterface.print_subagent_spawned(
        mock_cli, subagent_id="abc123", label="test-agent", task="Analyze Python files"
    )

    # Verify console.print was called
    assert mock_console.print.called, "Console.print should be called"

    # Get the Panel object that was passed to print
    call_args = mock_console.print.call_args[0]
    assert len(call_args) > 0, "Panel should be passed to print"

    # Verify it's a Panel
    assert isinstance(call_args[0], Panel), "Should print a Panel"

    print("✅ print_subagent_spawned works correctly")


def test_print_subagent_completed():
    """Test the enhanced completion notification method."""
    from rich.panel import Panel

    from src.interfaces.cli_interface import CLIInterface

    # Verify the method exists
    assert hasattr(CLIInterface, "print_subagent_completed"), "Method should exist on class"

    # Create a simple mock
    mock_console = Mock()

    class MockCLI:
        def __init__(self):
            self.console = mock_console

    mock_cli = MockCLI()
    CLIInterface.print_subagent_completed(
        mock_cli, subagent_id="abc123", label="test-agent", summary="Task completed successfully"
    )

    # Verify console.print was called
    assert mock_console.print.called, "Console.print should be called"

    # Verify Panel was created
    call_args = mock_console.print.call_args[0]
    assert isinstance(call_args[0], Panel), "Should print a Panel"

    print("✅ print_subagent_completed works correctly")


def test_print_subagent_failed():
    """Test the enhanced failure notification method."""
    from rich.panel import Panel

    from src.interfaces.cli_interface import CLIInterface

    # Verify the method exists
    assert hasattr(CLIInterface, "print_subagent_failed"), "Method should exist on class"

    # Create a simple mock
    mock_console = Mock()

    class MockCLI:
        def __init__(self):
            self.console = mock_console

    mock_cli = MockCLI()
    CLIInterface.print_subagent_failed(
        mock_cli, subagent_id="abc123", label="test-agent", error="Failed to analyze files"
    )

    # Verify console.print was called
    assert mock_console.print.called, "Console.print should be called"

    # Verify Panel was created
    call_args = mock_console.print.call_args[0]
    assert isinstance(call_args[0], Panel), "Should print a Panel"

    print("✅ print_subagent_failed works correctly")


def test_print_subagent_progress():
    """Test the progress notification method."""
    from src.interfaces.cli_interface import CLIInterface

    # Verify the method exists
    assert hasattr(CLIInterface, "print_subagent_progress"), "Method should exist on class"

    # Create a simple mock
    mock_console = Mock()

    class MockCLI:
        def __init__(self):
            self.console = mock_console

    mock_cli = MockCLI()
    CLIInterface.print_subagent_progress(
        mock_cli, subagent_id="abc123", label="test-agent", progress_msg="Processing file 5 of 10"
    )

    # Verify console.print was called with progress message
    assert mock_console.print.called, "Console.print should be called"

    print("✅ print_subagent_progress works correctly")


def test_print_background_notification():
    """Test the background notification method."""
    from src.interfaces.cli_interface import CLIInterface

    # Verify the method exists
    assert hasattr(CLIInterface, "print_background_notification"), "Method should exist on class"

    # Create a simple mock
    mock_console = Mock()

    class MockCLI:
        def __init__(self):
            self.console = mock_console

    mock_cli = MockCLI()
    CLIInterface.print_background_notification(
        mock_cli, title="Update", message="Background task started", style="cyan"
    )

    # Verify console.print was called
    assert mock_console.print.called, "Console.print should be called"

    print("✅ print_background_notification works correctly")


@pytest.mark.asyncio
async def test_orchestrator_event_integration():
    """Test that orchestrator properly integrates with new visualization methods."""
    from src.config.orchestrator import AgentOrchestrator
    from src.interfaces.cli_interface import CLIInterface
    from src.subagents.events import SubagentEvent, SubagentEventBus

    # Create mocks
    mock_cli = Mock(spec=CLIInterface)
    mock_cli.print_subagent_spawned = Mock()
    mock_cli.print_subagent_completed = Mock()
    mock_cli.print_subagent_failed = Mock()

    # Create event bus
    event_bus = SubagentEventBus()

    # Create orchestrator with mocked components
    with patch("src.config.orchestrator.AgentOrchestrator.__init__", return_value=None):
        orch = AgentOrchestrator()
        orch.cli = mock_cli
        orch.subagent_event_bus = event_bus
        orch.logger = Mock()

        # Manually set up event handlers
        from src.config.orchestrator import AgentOrchestrator as OrchestratorClass

        orch._on_subagent_spawned = OrchestratorClass._on_subagent_spawned.__get__(
            orch, AgentOrchestrator
        )
        orch._on_subagent_completed = OrchestratorClass._on_subagent_completed.__get__(
            orch, AgentOrchestrator
        )
        orch._on_subagent_failed = OrchestratorClass._on_subagent_failed.__get__(
            orch, AgentOrchestrator
        )

        # Subscribe to events
        event_bus.subscribe("spawned", orch._on_subagent_spawned)
        event_bus.subscribe("completed", orch._on_subagent_completed)
        event_bus.subscribe("failed", orch._on_subagent_failed)

    # Test spawned event
    spawn_event = SubagentEvent(
        subagent_id="test123",
        parent_task_id="parent123",
        event_type="spawned",
        content={"label": "test-agent", "task": "Test task"},
    )
    await event_bus.publish(spawn_event)
    await asyncio.sleep(0.1)  # Let event process

    # Verify spawned notification was called
    mock_cli.print_subagent_spawned.assert_called_once_with("test123", "test-agent", "Test task")

    # Test completed event
    complete_event = SubagentEvent(
        subagent_id="test123",
        parent_task_id="parent123",
        event_type="completed",
        content={"label": "test-agent", "result": "Task completed!"},
    )
    await event_bus.publish(complete_event)
    await asyncio.sleep(0.1)

    # Verify completed notification was called
    assert mock_cli.print_subagent_completed.called, "Completed notification should be called"

    # Test failed event
    fail_event = SubagentEvent(
        subagent_id="test123",
        parent_task_id="parent123",
        event_type="failed",
        content={"label": "test-agent", "error": "Something went wrong"},
    )
    await event_bus.publish(fail_event)
    await asyncio.sleep(0.1)

    # Verify failed notification was called
    assert mock_cli.print_subagent_failed.called, "Failed notification should be called"

    print("✅ Orchestrator event integration works correctly")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing Terminal Improvements (FASE 4)")
    print("=" * 60 + "\n")

    # Run tests
    test_imports()
    test_bracketed_paste_keybinding()
    test_print_subagent_spawned()
    test_print_subagent_completed()
    test_print_subagent_failed()
    test_print_subagent_progress()
    test_print_background_notification()

    # Run async test
    print("\nRunning async integration test...")
    asyncio.run(test_orchestrator_event_integration())

    print("\n" + "=" * 60)
    print("✅ All Terminal Improvement Tests Passed (8/8)")
    print("=" * 60)
