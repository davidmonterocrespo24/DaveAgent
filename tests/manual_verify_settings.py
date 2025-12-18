
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.settings import DaveAgentSettings


def test_deepseek_defaults():
    print("Testing DeepSeek defaults...")
    # Simulate DeepSeek URL
    settings = DaveAgentSettings(base_url="https://api.deepseek.com", api_key="test")

    assert settings.base_model == "deepseek-chat", f"Expected base_model='deepseek-chat', got '{settings.base_model}'"
    assert settings.strong_model == "deepseek-reasoner", f"Expected strong_model='deepseek-reasoner', got '{settings.strong_model}'"
    print("✅ DeepSeek defaults passed")

def test_openai_defaults():
    print("Testing OpenAI defaults...")
    # Simulate OpenAI (should fallback to model name if not specified)
    settings = DaveAgentSettings(base_url="https://api.openai.com", model="gpt-4o", api_key="test")

    assert settings.base_model == "gpt-4o", f"Expected base_model='gpt-4o', got '{settings.base_model}'"
    assert settings.strong_model == "gpt-4o", f"Expected strong_model='gpt-4o', got '{settings.strong_model}'"
    print("✅ OpenAI defaults passed (fallback behavior)")

def test_env_override():
    print("Testing ENV overrides...")
    os.environ["DAVEAGENT_BASE_MODEL"] = "custom-base"
    os.environ["DAVEAGENT_STRONG_MODEL"] = "custom-strong"

    settings = DaveAgentSettings(base_url="https://api.deepseek.com", api_key="test")

    assert settings.base_model == "custom-base", f"Expected 'custom-base', got '{settings.base_model}'"
    assert settings.strong_model == "custom-strong", f"Expected 'custom-strong', got '{settings.strong_model}'"

    # Cleanup
    del os.environ["DAVEAGENT_BASE_MODEL"]
    del os.environ["DAVEAGENT_STRONG_MODEL"]
    print("✅ ENV overrides passed")

if __name__ == "__main__":
    try:
        test_deepseek_defaults()
        test_openai_defaults()
        test_env_override()
        print("\n✨ All settings tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
