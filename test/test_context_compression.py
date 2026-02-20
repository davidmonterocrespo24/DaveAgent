"""
Test script for context compression and token counting.

Tests:
1. Token counting accuracy
2. Compression trigger at 80% threshold
3. Summary quality preservation
4. DeepSeek model integration

Usage:
    python -m test.test_context_compression
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.token_counter import (
    count_message_tokens,
    get_model_context_limit,
    should_compress_context,
    get_token_usage_stats,
)
from src.utils.context_compressor import (
    select_messages_to_compress,
    estimate_compression_ratio,
)


def test_token_counting():
    """Test 1: Verify token counting accuracy."""
    print("=" * 70)
    print("TEST 1: Token Counting Accuracy")
    print("=" * 70)

    # Simple test messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "user", "content": "Can you explain quantum computing in simple terms?"},
    ]

    model = "deepseek-chat"
    token_count = count_message_tokens(messages, model)
    max_tokens = get_model_context_limit(model)

    print(f"\n📊 Message count: {len(messages)}")
    print(f"📊 Token count: {token_count}")
    print(f"📊 Model limit: {max_tokens}")
    print(f"📊 Usage: {(token_count/max_tokens)*100:.2f}%")

    # Verify reasonable token count (rough estimate)
    total_chars = sum(len(msg["content"]) for msg in messages)
    estimated_tokens = total_chars // 4  # Rough estimate: 1 token ≈ 4 chars

    print(f"\n✅ Total characters: {total_chars}")
    print(f"✅ Estimated tokens (chars/4): {estimated_tokens}")
    print(f"✅ Actual tokens: {token_count}")
    print(f"✅ Difference: {abs(token_count - estimated_tokens)} tokens")

    if estimated_tokens * 0.5 <= token_count <= estimated_tokens * 2:
        print("✅ PASS: Token count is within expected range")
        return True
    else:
        print("❌ FAIL: Token count seems off")
        return False


def test_compression_threshold():
    """Test 2: Verify compression triggers at correct threshold."""
    print("\n" + "=" * 70)
    print("TEST 2: Compression Threshold Detection")
    print("=" * 70)

    model = "deepseek-chat"
    max_tokens = get_model_context_limit(model)

    # Create messages that are below threshold
    small_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]

    should_compress_small = should_compress_context(small_messages, model, threshold=0.8)
    tokens_small = count_message_tokens(small_messages, model)

    print(f"\n📊 Small conversation:")
    print(f"   Messages: {len(small_messages)}")
    print(f"   Tokens: {tokens_small}/{max_tokens} ({(tokens_small/max_tokens)*100:.2f}%)")
    print(f"   Should compress: {should_compress_small}")

    if not should_compress_small:
        print("✅ PASS: Small conversation not flagged for compression")
    else:
        print("❌ FAIL: Small conversation incorrectly flagged")
        return False

    # Create messages that simulate 85% usage (above 80% threshold)
    # Each message ~500 tokens, need ~111,411 tokens (85% of 131,072)
    target_tokens = int(max_tokens * 0.85)
    large_content = "This is a test message. " * 200  # ~500 tokens per message

    # Calculate how many messages we need
    tokens_per_message = count_message_tokens(
        [{"role": "user", "content": large_content}], model
    )
    num_messages_needed = target_tokens // tokens_per_message

    print(f"\n📊 Creating large conversation to test threshold...")
    print(f"   Target tokens: {target_tokens} (85% of max)")
    print(f"   Tokens per message: {tokens_per_message}")
    print(f"   Messages needed: {num_messages_needed}")

    large_messages = []
    for i in range(num_messages_needed):
        role = "user" if i % 2 == 0 else "assistant"
        large_messages.append({"role": role, "content": large_content})

    should_compress_large = should_compress_context(large_messages, model, threshold=0.8)
    tokens_large = count_message_tokens(large_messages, model)

    print(f"\n📊 Large conversation:")
    print(f"   Messages: {len(large_messages)}")
    print(f"   Tokens: {tokens_large}/{max_tokens} ({(tokens_large/max_tokens)*100:.2f}%)")
    print(f"   Should compress: {should_compress_large}")

    if should_compress_large:
        print("✅ PASS: Large conversation correctly flagged for compression")
        return True
    else:
        print("❌ FAIL: Large conversation not flagged (threshold not working)")
        return False


def test_message_selection():
    """Test 3: Verify message selection for compression."""
    print("\n" + "=" * 70)
    print("TEST 3: Message Selection for Compression")
    print("=" * 70)

    # Create a conversation with system + user/assistant messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
        {"role": "user", "content": "Message 3"},
        {"role": "assistant", "content": "Response 3"},
        {"role": "user", "content": "Message 4 (recent)"},
        {"role": "assistant", "content": "Response 4 (recent)"},
    ]

    keep_recent = 4  # Keep last 4 messages
    to_compress, to_keep = select_messages_to_compress(messages, keep_recent)

    print(f"\n📊 Original messages: {len(messages)}")
    print(f"📊 Keep recent: {keep_recent}")
    print(f"📊 Messages to compress: {len(to_compress)}")
    print(f"📊 Messages to keep: {len(to_keep)}")

    print("\n📋 Messages to compress:")
    for msg in to_compress:
        print(f"   - [{msg['role']}]: {msg['content']}")

    print("\n📋 Messages to keep:")
    for msg in to_keep:
        print(f"   - [{msg['role']}]: {msg['content']}")

    # Verify system message is kept
    system_messages_kept = [msg for msg in to_keep if msg["role"] == "system"]
    recent_messages_kept = [msg for msg in to_keep if msg["role"] != "system"]

    print("\n✅ Verification:")
    print(f"   System messages kept: {len(system_messages_kept)}")
    print(f"   Recent messages kept: {len(recent_messages_kept)}")

    if len(system_messages_kept) == 1 and len(recent_messages_kept) == keep_recent:
        print("✅ PASS: Message selection is correct")
        return True
    else:
        print("❌ FAIL: Message selection incorrect")
        return False


def test_token_usage_stats():
    """Test 4: Verify token usage statistics."""
    print("\n" + "=" * 70)
    print("TEST 4: Token Usage Statistics")
    print("=" * 70)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! " * 100},  # ~100 tokens
        {"role": "assistant", "content": "Hi there! " * 100},  # ~100 tokens
    ]

    model = "deepseek-chat"
    stats = get_token_usage_stats(messages, model)

    print(f"\n📊 Token Usage Statistics:")
    print(f"   Current tokens: {stats['current_tokens']}")
    print(f"   Max tokens: {stats['max_tokens']}")
    print(f"   Usage ratio: {stats['usage_ratio']:.2%}")
    print(f"   Messages count: {stats['messages_count']}")
    print(f"   Avg tokens/message: {stats['avg_tokens_per_message']:.1f}")

    # Calculate derived values
    remaining_tokens = stats['max_tokens'] - stats['current_tokens']
    should_compress = should_compress_context(messages, model, threshold=0.8)

    print(f"   Remaining tokens: {remaining_tokens}")
    print(f"   Should compress (80%): {should_compress}")

    # Verify stats are reasonable
    if (
        stats["current_tokens"] > 0
        and stats["max_tokens"] == 131072
        and stats["usage_ratio"] < 1.0
        and remaining_tokens > 0
    ):
        print("✅ PASS: Token usage stats are correct")
        return True
    else:
        print("❌ FAIL: Token usage stats incorrect")
        return False


def test_compression_ratio_estimate():
    """Test 5: Verify compression ratio estimation."""
    print("\n" + "=" * 70)
    print("TEST 5: Compression Ratio Estimation")
    print("=" * 70)

    messages = [
        {"role": "user", "content": "Message " * 50},  # ~50 tokens
        {"role": "assistant", "content": "Response " * 50},  # ~50 tokens
    ] * 10  # 20 messages total

    keep_recent = 5

    ratio = estimate_compression_ratio(messages, keep_recent)

    print(f"\n📊 Compression Estimation:")
    print(f"   Total messages: {len(messages)}")
    print(f"   Keep recent: {keep_recent}")
    print(f"   Estimated compression ratio: {ratio:.2%}")

    # Ratio should be between 0.1 and 0.9 (10% to 90% size reduction)
    if 0.1 <= ratio <= 0.9:
        print(f"✅ PASS: Compression ratio ({ratio:.2%}) is reasonable")
        return True
    else:
        print(f"❌ FAIL: Compression ratio ({ratio:.2%}) seems off")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 70)
    print("🧪 CONTEXT COMPRESSION TEST SUITE")
    print("=" * 70)
    print("Testing token counting and compression functionality...\n")

    tests = [
        ("Token Counting Accuracy", test_token_counting),
        ("Compression Threshold", test_compression_threshold),
        ("Message Selection", test_message_selection),
        ("Token Usage Stats", test_token_usage_stats),
        ("Compression Ratio", test_compression_ratio_estimate),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 70)
    print(f"Results: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
