"""
Test for message filtering in stream processing.

This test diagnoses why TextMessage responses from agents aren't showing in the console.
"""

import os
import sys

# Fix encoding for Windows console
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from autogen_agentchat.messages import TextMessage


def test_text_message_source_attribute():
    """Test that TextMessage objects have a 'source' attribute."""
    # Create a TextMessage
    msg = TextMessage(content="Test response", source="Coder")

    print(f"✓ TextMessage has 'source' attribute: {hasattr(msg, 'source')}")
    print(f"✓ Source value: {msg.source}")
    print(f"✓ Message type: {type(msg).__name__}")

    assert hasattr(msg, "source"), "TextMessage should have 'source' attribute"
    assert msg.source == "Coder", "Source should be 'Coder'"


def test_message_filtering_logic():
    """Test the filtering logic used in process_user_request."""

    test_cases = [
        # (source, should_process, description)
        ("user", False, "Messages from 'user' should be filtered out"),
        ("Coder", True, "Messages from 'Coder' should be processed"),
        ("Planner", True, "Messages from 'Planner' should be processed"),
        ("unknown", True, "Messages from 'unknown' should be processed"),
        (None, False, "Messages with None source should be filtered"),
    ]

    for source, should_process, description in test_cases:
        # Create message with specific source
        if source is None:
            # Message without source attribute
            msg = MagicMock()
            delattr(msg, "source")
        else:
            msg = TextMessage(content="Test", source=source)

        # Apply the filtering logic from main.py line 1615
        passes_filter = hasattr(msg, "source") and msg.source != "user"

        print(f"{'✓' if passes_filter == should_process else '✗'} {description}")
        print(
            f"  Source: {getattr(msg, 'source', 'NO ATTRIBUTE')}, Passes filter: {passes_filter}, Expected: {should_process}"
        )

        if passes_filter != should_process:
            print(f"  ⚠️  MISMATCH! Expected {should_process} but got {passes_filter}")


def test_message_stream_simulation():
    """Simulate a stream of messages to see what gets filtered."""

    # Simulate typical message stream from agents
    messages = [
        TextMessage(content="User input", source="user"),  # Should be filtered
        TextMessage(content="I'll help with that", source="Planner"),  # Should show
        TextMessage(content="Reading files...", source="Coder"),  # Should show
        TextMessage(content="Here's the result", source="Coder"),  # Should show
    ]

    print("\n=== Simulating Message Stream ===")
    message_count = 0
    processed_count = 0

    for msg in messages:
        message_count += 1
        msg_type = type(msg).__name__
        msg_source = getattr(msg, "source", "unknown")

        print(f"\nMessage #{message_count}:")
        print(f"  Type: {msg_type}")
        print(f"  Source: {msg_source}")
        print(f"  Content: {msg.content[:50]}...")

        # Apply filter
        if hasattr(msg, "source") and msg.source != "user":
            processed_count += 1
            print("  ✓ PROCESSED (would show in console)")
        else:
            print("  ✗ FILTERED (would NOT show in console)")

    print("\n=== Summary ===")
    print(f"Total messages: {message_count}")
    print(f"Processed: {processed_count}")
    print(f"Filtered: {message_count - processed_count}")

    assert processed_count == 3, f"Expected 3 messages to be processed, got {processed_count}"


async def test_real_message_from_selector():
    """Test what source a message from SelectorGroupChat actually has."""

    print("\n=== Testing Real SelectorGroupChat Message ===")

    # This would require actually running the agent, so we'll mock it
    # The key question: does the message from Planner/Coder after tool execution
    # have source="Planner" or source="Coder", or something else?

    # Based on AutoGen docs, messages from agents in a GroupChat should have
    # source set to the agent's name

    print("ℹ️  According to AutoGen documentation:")
    print("  - Messages from AssistantAgent should have source='<agent_name>'")
    print("  - In our case: source='Planner' or source='Coder'")
    print("  - These should NOT be filtered by the condition")
    print("\n⚠️  If messages are still being filtered, possible causes:")
    print("  1. The message doesn't have a 'source' attribute")
    print("  2. The source is 'user' (shouldn't happen for agent messages)")
    print("  3. The message is a different type that we're not handling")


def test_message_key_generation():
    """Test the message key generation logic to avoid duplicates."""

    print("\n=== Testing Message Key Generation ===")

    # Same content from same agent should generate same key
    msg1 = TextMessage(content="Test response", source="Coder")
    msg2 = TextMessage(content="Test response", source="Coder")

    # Different content from same agent should generate different keys
    msg3 = TextMessage(content="Different response", source="Coder")

    # Same content from different agent should generate different keys
    msg4 = TextMessage(content="Test response", source="Planner")

    agent_messages_shown = set()

    for i, msg in enumerate([msg1, msg2, msg3, msg4], 1):
        agent_name = msg.source
        content_str = msg.content
        message_key = f"{agent_name}:{hash(content_str)}"

        is_duplicate = message_key in agent_messages_shown
        agent_messages_shown.add(message_key)

        print(f"Message {i}: source={agent_name}, duplicate={is_duplicate}")
        print(f"  Key: {message_key}")

    print(f"\n✓ Unique messages tracked: {len(agent_messages_shown)}")
    assert len(agent_messages_shown) == 3, "Should have 3 unique messages (msg1=msg2)"


if __name__ == "__main__":
    print("=" * 70)
    print("MESSAGE FILTERING DIAGNOSTIC TESTS")
    print("=" * 70)

    print("\n[TEST 1] TextMessage Source Attribute")
    print("-" * 70)
    test_text_message_source_attribute()

    print("\n[TEST 2] Message Filtering Logic")
    print("-" * 70)
    test_message_filtering_logic()

    print("\n[TEST 3] Message Stream Simulation")
    print("-" * 70)
    test_message_stream_simulation()

    print("\n[TEST 4] Real Message Source")
    print("-" * 70)
    asyncio.run(test_real_message_from_selector())

    print("\n[TEST 5] Message Key Generation")
    print("-" * 70)
    test_message_key_generation()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)

    print("\n📋 NEXT STEPS:")
    print("1. Run the actual agent with debug logging enabled")
    print("2. Check the logs for 'Stream mensaje' lines with Source info")
    print("3. Look for TextMessage types that have source != user but aren't showing")
    print("4. If found, the issue is in the console display logic, not the filter")
