"""
Model Settings - Model and provider configuration
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelProvider:
    """Model provider information"""

    name: str
    display_name: str
    base_url: str
    default_model: str
    models: list[str]
    requires_api_key: bool
    api_key_url: str
    capabilities: dict[str, Any]


# Supported provider definitions
PROVIDERS = {
    "deepseek": ModelProvider(
        name="deepseek",
        display_name="DeepSeek (Recommended - Fast and affordable)",
        base_url="https://api.deepseek.com",
        default_model="deepseek-reasoner",
        models=["deepseek-chat", "deepseek-reasoner"],
        requires_api_key=True,
        api_key_url="https://platform.deepseek.com/api_keys",
        capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        },
    ),
    "openai": ModelProvider(
        name="openai",
        display_name="OpenAI (GPT-4 - Powerful but expensive)",
        base_url="https://api.openai.com/v1",
        default_model="gpt-5",
        models=["gpt-5", "gpt-5-mini"],
        requires_api_key=True,
        api_key_url="https://platform.openai.com/api-keys",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        },
    ),
    "azure": ModelProvider(
        name="azure",
        display_name="Azure OpenAI",
        base_url="",  # User must provide
        default_model="gpt-4o",
        models=["gpt-4o", "gpt-4", "gpt-35-turbo"],
        requires_api_key=True,
        api_key_url="https://portal.azure.com",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        },
    ),
    "anthropic": ModelProvider(
        name="anthropic",
        display_name="Anthropic (Claude)",
        base_url="https://api.anthropic.com",
        default_model="claude-3-7-sonnet-20250219",
        models=[
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
        ],
        requires_api_key=True,
        api_key_url="https://console.anthropic.com/settings/keys",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        },
    ),
    "ollama": ModelProvider(
        name="ollama",
        display_name="Ollama (Local - Free)",
        base_url="http://localhost:11434/v1",
        default_model="llama3.2",
        models=["llama3.2", "llama3.1", "mistral", "codellama", "phi3"],
        requires_api_key=False,
        api_key_url="",
        capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        },
    ),
    "gemini": ModelProvider(
        name="gemini",
        display_name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        default_model="gemini-1.5-flash",
        models=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
        requires_api_key=True,
        api_key_url="https://makersuite.google.com/app/apikey",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        },
    ),
    "llama": ModelProvider(
        name="llama",
        display_name="Llama API (Meta)",
        base_url="https://api.llama-api.com",
        default_model="Llama-4-Scout-17B-16E-Instruct-FP8",
        models=["Llama-4-Scout-17B-16E-Instruct-FP8", "Llama-4-Maverick-17B-128E-Instruct-FP8"],
        requires_api_key=True,
        api_key_url="https://www.llama-api.com/",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        },
    ),
}


def show_providers_menu() -> str:
    """
    Shows the provider menu and returns the selection

    Returns:
        Selected provider name
    """
    print()
    print("🌐 AI Provider Selection")
    print("=" * 70)
    print()
    print("Select the provider you want to use:")
    print()

    # List providers
    providers_list = list(PROVIDERS.keys())
    for i, provider_key in enumerate(providers_list, 1):
        provider = PROVIDERS[provider_key]
        cost_info = ""
        if provider.requires_api_key:
            if "deepseek" in provider_key.lower():
                cost_info = " [Free to start]"
            elif "ollama" in provider_key.lower():
                cost_info = " [Free - Local]"
            elif "openai" in provider_key.lower():
                cost_info = " [Paid]"
        else:
            cost_info = " [Free]"

        print(f"  {i}. {provider.display_name}{cost_info}")

    print()

    while True:
        try:
            choice = input(f"Select an option (1-{len(providers_list)}): ").strip()

            if not choice:
                print("❌ You must select an option.")
                continue

            choice_num = int(choice)

            if 1 <= choice_num <= len(providers_list):
                selected = providers_list[choice_num - 1]
                return selected
            else:
                print(f"❌ Invalid option. Select between 1 and {len(providers_list)}.")

        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\n❌ Selection cancelled.")
            raise


def show_models_menu(provider_name: str) -> str:
    """
    Shows the model menu for a provider

    Args:
        provider_name: Provider name

    Returns:
        Selected model name
    """
    provider = PROVIDERS[provider_name]

    print()
    print(f"📊 Model Selection ({provider.display_name})")
    print("=" * 70)
    print()
    print("Available models:")
    print()

    for i, model in enumerate(provider.models, 1):
        default_mark = " (Default)" if model == provider.default_model else ""
        print(f"  {i}. {model}{default_mark}")

    print()
    print(f"  0. Use default model ({provider.default_model})")
    print()

    while True:
        try:
            choice = input(f"Select an option (0-{len(provider.models)}): ").strip()

            if not choice or choice == "0":
                return provider.default_model

            choice_num = int(choice)

            if 1 <= choice_num <= len(provider.models):
                return provider.models[choice_num - 1]
            else:
                print(f"❌ Invalid option. Select between 0 and {len(provider.models)}.")

        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\n❌ Selection cancelled.")
            raise


def configure_azure_settings() -> dict[str, str]:
    """
    Configures Azure-specific settings

    Returns:
        Dictionary with Azure configuration
    """
    print()
    print("⚙️  Azure OpenAI Configuration")
    print("=" * 70)
    print()
    print("To use Azure OpenAI you need to provide:")
    print()

    endpoint = input("Azure Endpoint (e.g.: https://your-resource.openai.azure.com/): ").strip()
    deployment = input("Deployment Name: ").strip()
    api_version = input("API Version (default: 2024-06-01): ").strip() or "2024-06-01"

    return {
        "azure_endpoint": endpoint,
        "azure_deployment": deployment,
        "api_version": api_version,
    }


def get_provider_info(provider_name: str) -> ModelProvider:
    """
    Gets provider information

    Args:
        provider_name: Provider name

    Returns:
        Provider information
    """
    return PROVIDERS.get(provider_name, PROVIDERS["deepseek"])


def interactive_model_selection() -> tuple[str, str, str, dict[str, str] | None]:
    """
    Interactive provider and model selection

    Returns:
        Tuple (provider_name, base_url, model_name, extra_config)
    """
    # Select provider
    provider_name = show_providers_menu()
    provider = PROVIDERS[provider_name]

    # Show provider information
    print()
    print("=" * 70)
    print(f"✓ Provider selected: {provider.display_name}")

    if provider.requires_api_key:
        print("  API Key required: Yes")
        print(f"  Get API key at: {provider.api_key_url}")
    else:
        print("  API Key required: No")

    # Select model
    model_name = show_models_menu(provider_name)

    print(f"✓ Model selected: {model_name}")
    print("=" * 70)

    # Extra configuration for Azure
    extra_config = None
    if provider_name == "azure":
        extra_config = configure_azure_settings()

    base_url = provider.base_url

    return provider_name, base_url, model_name, extra_config
