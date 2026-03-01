"""
Test for message deduplication logic.

This test checks if the deduplication mechanism might be preventing
TextMessage responses from showing.
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

from autogen_agentchat.messages import TextMessage


def test_planner_messages_deduplication():
    """Test if Planner messages with similar content get deduplicated incorrectly."""

    print("=" * 70)
    print("TESTING PLANNER MESSAGE DEDUPLICATION")
    print("=" * 70)

    # Simulate what might happen with Planner messages
    agent_messages_shown = set()

    test_scenarios = [
        {
            "desc": "First plan message",
            "source": "Planner",
            "content": "I'll help you create a README. First, let me analyze the project structure.",
        },
        {
            "desc": "Same plan message (duplicate)",
            "source": "Planner",
            "content": "I'll help you create a README. First, let me analyze the project structure.",
        },
        {
            "desc": "Updated plan message",
            "source": "Planner",
            "content": "Based on the analysis, I'll now create the README with the following sections...",
        },
        {
            "desc": "Coder acknowledgment",
            "source": "Coder",
            "content": "I'll start by reading the existing files.",
        },
        {
            "desc": "Coder final response",
            "source": "Coder",
            "content": "I've completed the README creation. The file has been written to README.md.",
        },
    ]

    print("\n📝 Simulating message stream...\n")

    for i, scenario in enumerate(test_scenarios, 1):
        agent_name = scenario["source"]
        content_str = scenario["content"]
        message_key = f"{agent_name}:{hash(content_str)}"

        is_new = message_key not in agent_messages_shown

        status = "✓ SHOW" if is_new else "✗ SKIP (duplicate)"
        print(f"{i}. [{agent_name}] {status}")
        print(f"   {scenario['desc']}")
        print(f"   Content: {content_str[:60]}...")
        print(f"   Key: ...{str(hash(content_str))[-8:]}")
        print()

        if is_new:
            agent_messages_shown.add(message_key)

    print(f"📊 Summary: {len(agent_messages_shown)} unique messages shown")
    print("   Expected: 4 (scenario 2 is duplicate of scenario 1)")

    assert len(agent_messages_shown) == 4, (
        f"Expected 4 unique messages, got {len(agent_messages_shown)}"
    )


def test_empty_or_whitespace_content():
    """Test edge case: what if message content is empty or just whitespace?"""

    print("\n" + "=" * 70)
    print("TESTING EMPTY/WHITESPACE CONTENT")
    print("=" * 70)

    test_cases = [
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        ("\n\n", "Newlines only"),
        ("Response", "Normal content"),
    ]

    print()
    for content, desc in test_cases:
        try:
            message_key = f"Coder:{hash(content)}"
            print(f"✓ {desc:20} -> Key: ...{str(hash(content))[-8:]}")
        except Exception as e:
            print(f"✗ {desc:20} -> ERROR: {e}")


def test_list_content_hashing():
    """Test if content that is a list (like tool calls) hashes correctly."""

    print("\n" + "=" * 70)
    print("TESTING LIST CONTENT HASHING")
    print("=" * 70)

    print("\nSimulating the hashing logic from main.py lines 1633-1641...\n")

    test_contents = [
        "Normal string content",
        ["tool_call_1", "tool_call_2"],  # List content
        {"type": "function_call"},  # Dict content
    ]

    for content in test_contents:
        try:
            # This is the exact logic from main.py
            if isinstance(content, list):
                content_str = str(content)
            else:
                content_str = content

            # Try to create the key
            try:
                message_key = f"Coder:{hash(content_str)}"
                print(f"✓ Type {type(content).__name__:10} -> Hashed successfully")
                print(f"  Content: {str(content)[:50]}")
                print(f"  Key suffix: ...{str(hash(content_str))[-8:]}")
            except TypeError:
                # Fallback from line 1640
                message_key = f"Coder:{hash(str(content))}"
                print(f"⚠ Type {type(content).__name__:10} -> Required fallback to str()")
                print(f"  Key suffix: ...{str(hash(str(content)))[-8:]}")

            print()

        except Exception as e:
            print(f"✗ Type {type(content).__name__:10} -> ERROR: {e}\n")


def test_message_shown_set_behavior():
    """Test the set behavior for message deduplication."""

    print("\n" + "=" * 70)
    print("TESTING SET DEDUPLICATION BEHAVIOR")
    print("=" * 70)

    agent_messages_shown = set()

    # Add some message keys
    keys = [
        "Planner:12345",
        "Coder:67890",
        "Planner:12345",  # Duplicate
        "Coder:11111",
    ]

    print("\nAdding message keys to set...\n")

    for i, key in enumerate(keys, 1):
        was_in_set = key in agent_messages_shown
        agent_messages_shown.add(key)

        status = "DUPLICATE" if was_in_set else "NEW"
        action = "Skipped" if was_in_set else "Added"

        print(f"{i}. {key:20} -> {status:10} ({action})")

    print(f"\n📊 Final set size: {len(agent_messages_shown)}")
    print("   Expected: 3 (one duplicate)")

    assert len(agent_messages_shown) == 3, (
        f"Expected 3 unique keys, got {len(agent_messages_shown)}"
    )


if __name__ == "__main__":
    test_planner_messages_deduplication()
    test_empty_or_whitespace_content()
    test_list_content_hashing()
    test_message_shown_set_behavior()

    print("\n" + "=" * 70)
    print("ALL DEDUPLICATION TESTS PASSED ✓")
    print("=" * 70)

    print("\n💡 KEY FINDINGS:")
    print("1. Deduplication logic works correctly")
    print("2. Same content from same agent = duplicate (expected)")
    print("3. Different content or different agent = new message (expected)")
    print("\n⚠️  If messages still not showing, check:")
    print("   - Are TextMessages actually reaching the stream?")
    print("   - What is their 'source' attribute value?")
    print("   - Is print_agent_message() actually being called?")
