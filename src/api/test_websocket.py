#!/usr/bin/env python3
"""
Simple WebSocket client for testing DaveAgent API
Run: python src/api/test_websocket.py
"""

import asyncio
import json

try:
    import websockets
except ImportError:
    print("❌ Error: websockets library not installed")
    print("💡 Install with: pip install websockets")
    exit(1)


async def test_websocket():
    """Test WebSocket connection and basic commands"""
    uri = "ws://localhost:8000/ws/agent"

    print("=" * 70)
    print("🧪 DaveAgent WebSocket Test Client")
    print("=" * 70)
    print(f"📡 Connecting to: {uri}")
    print()

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            print("\n" + "=" * 70)

            # Receive connection event
            response = await websocket.recv()
            event = json.loads(response)
            print(f"📥 Received event:")
            print(json.dumps(event, indent=2))
            print("=" * 70)

            # Test commands
            test_commands = [
                {"command": "execute", "content": "/help", "description": "Request help"},
                {
                    "command": "execute",
                    "content": "What is DaveAgent?",
                    "description": "Ask a question",
                },
                {"command": "list_sessions", "description": "List sessions"},
            ]

            for i, test in enumerate(test_commands, 1):
                print(f"\n📤 Test {i}: {test['description']}")
                print(f"   Sending: {test}")

                # Remove description before sending
                message = {k: v for k, v in test.items() if k != "description"}
                await websocket.send(json.dumps(message))

                print(f"\n   Waiting for responses...")

                # Receive responses (with timeout)
                try:
                    responses_count = 0
                    while responses_count < 5:  # Limit responses per command
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        event = json.loads(response)

                        # Pretty print event
                        event_type = event.get("type", "unknown")
                        timestamp = event.get("timestamp", "")

                        print(f"\n   📥 [{event_type}] at {timestamp}")

                        # Show relevant fields based on type
                        if event_type == "agent_message":
                            print(f"      Agent: {event.get('agent')}")
                            print(f"      Content: {event.get('content')[:100]}...")
                        elif event_type == "thinking":
                            print(f"      Agent: {event.get('agent')}")
                            print(f"      Thinking: {event.get('content')}")
                        elif event_type == "tool_call":
                            print(f"      Tool: {event.get('tool_name')}")
                            print(f"      Agent: {event.get('agent')}")
                        elif event_type == "error":
                            print(f"      Error: {event.get('message')}")
                        elif event_type == "success":
                            print(f"      Success: {event.get('message')}")
                        elif event_type == "sessions_list":
                            sessions = event.get("sessions", [])
                            print(f"      Total sessions: {len(sessions)}")
                            for session in sessions[:3]:  # Show first 3
                                print(
                                    f"        - {session.get('session_id')}: {session.get('title', 'Untitled')}"
                                )

                        responses_count += 1

                        # Stop receiving if we get a success or goodbye
                        if event_type in ["success", "goodbye", "sessions_list"]:
                            break

                except asyncio.TimeoutError:
                    print("   ⏱️  Timeout waiting for response")

                print("   " + "-" * 66)

            print("\n" + "=" * 70)
            print("✅ All tests completed!")
            print("=" * 70)

    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket error: {e}")
        print("\n💡 Make sure the server is running:")
        print("   daveagent --server")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


async def interactive_mode():
    """Interactive WebSocket client"""
    uri = "ws://localhost:8000/ws/agent"

    print("=" * 70)
    print("💬 DaveAgent Interactive WebSocket Client")
    print("=" * 70)
    print(f"📡 Connecting to: {uri}")
    print()

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            print("💡 Type your messages and press Enter. Type 'exit' to quit.\n")

            # Start task to receive messages
            async def receive_messages():
                try:
                    while True:
                        response = await websocket.recv()
                        event = json.loads(response)
                        event_type = event.get("type", "unknown")

                        # Format output based on event type
                        if event_type == "agent_message":
                            print(f"\n🤖 {event.get('agent')}: {event.get('content')}\n")
                        elif event_type == "thinking":
                            print(f"💭 {event.get('agent')}: {event.get('content')}")
                        elif event_type == "error":
                            print(f"\n❌ Error: {event.get('message')}\n")
                        elif event_type == "success":
                            print(f"\n✅ {event.get('message')}\n")
                        elif event_type == "info":
                            print(f"ℹ️  {event.get('message')}")
                        else:
                            print(f"\n📥 [{event_type}]: {json.dumps(event, indent=2)}\n")

                        print("You: ", end="", flush=True)

                except Exception as e:
                    print(f"\n❌ Receive error: {e}")

            # Start receiver task
            receiver_task = asyncio.create_task(receive_messages())

            # Input loop
            try:
                while True:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "You: "
                    )

                    if user_input.strip().lower() in ["exit", "quit"]:
                        print("\n👋 Goodbye!")
                        break

                    if user_input.strip():
                        await websocket.send(
                            json.dumps({"command": "execute", "content": user_input})
                        )

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")

            # Cancel receiver task
            receiver_task.cancel()

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print("Starting interactive mode...")
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_websocket())
