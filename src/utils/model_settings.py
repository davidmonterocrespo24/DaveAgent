"""
Model Settings - Configuración de modelos y proveedores
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ModelProvider:
    """Información de un proveedor de modelos"""
    name: str
    display_name: str
    base_url: str
    default_model: str
    models: list[str]
    requires_api_key: bool
    api_key_url: str
    capabilities: Dict[str, Any]


# Definición de proveedores soportados
PROVIDERS = {
    "deepseek": ModelProvider(
        name="deepseek",
        display_name="DeepSeek (Recomendado - Rápido y económico)",
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
        }
    ),
    "openai": ModelProvider(
        name="openai",
        display_name="OpenAI (GPT-4 - Potente pero costoso)",
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
        }
    ),
    "azure": ModelProvider(
        name="azure",
        display_name="Azure OpenAI",
        base_url="",  # Usuario debe proporcionar
        default_model="gpt-4o",
        models=["gpt-4o", "gpt-4", "gpt-35-turbo"],
        requires_api_key=True,
        api_key_url="https://portal.azure.com",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        }
    ),
    "anthropic": ModelProvider(
        name="anthropic",
        display_name="Anthropic (Claude)",
        base_url="https://api.anthropic.com",
        default_model="claude-3-7-sonnet-20250219",
        models=[
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229"
        ],
        requires_api_key=True,
        api_key_url="https://console.anthropic.com/settings/keys",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
    ),
    "ollama": ModelProvider(
        name="ollama",
        display_name="Ollama (Local - Gratis)",
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
        }
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
        }
    ),
    "llama": ModelProvider(
        name="llama",
        display_name="Llama API (Meta)",
        base_url="https://api.llama-api.com",
        default_model="Llama-4-Scout-17B-16E-Instruct-FP8",
        models=[
            "Llama-4-Scout-17B-16E-Instruct-FP8",
            "Llama-4-Maverick-17B-128E-Instruct-FP8"
        ],
        requires_api_key=True,
        api_key_url="https://www.llama-api.com/",
        capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
        }
    ),
}


def show_providers_menu() -> str:
    """
    Muestra el menú de proveedores y retorna la selección

    Returns:
        Nombre del proveedor seleccionado
    """
    print()
    print("🌐 Selección de Proveedor de IA")
    print("=" * 70)
    print()
    print("Selecciona el proveedor que quieres usar:")
    print()

    # Listar proveedores
    providers_list = list(PROVIDERS.keys())
    for i, provider_key in enumerate(providers_list, 1):
        provider = PROVIDERS[provider_key]
        cost_info = ""
        if provider.requires_api_key:
            if "deepseek" in provider_key.lower():
                cost_info = " [Gratis para empezar]"
            elif "ollama" in provider_key.lower():
                cost_info = " [Gratis - Local]"
            elif "openai" in provider_key.lower():
                cost_info = " [Pago]"
        else:
            cost_info = " [Gratis]"

        print(f"  {i}. {provider.display_name}{cost_info}")

    print()

    while True:
        try:
            choice = input(f"Selecciona una opción (1-{len(providers_list)}): ").strip()

            if not choice:
                print("❌ Debes seleccionar una opción.")
                continue

            choice_num = int(choice)

            if 1 <= choice_num <= len(providers_list):
                selected = providers_list[choice_num - 1]
                return selected
            else:
                print(f"❌ Opción inválida. Selecciona entre 1 y {len(providers_list)}.")

        except ValueError:
            print("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            print("\n\n❌ Selección cancelada.")
            raise


def show_models_menu(provider_name: str) -> str:
    """
    Muestra el menú de modelos para un proveedor

    Args:
        provider_name: Nombre del proveedor

    Returns:
        Nombre del modelo seleccionado
    """
    provider = PROVIDERS[provider_name]

    print()
    print(f"📊 Selección de Modelo ({provider.display_name})")
    print("=" * 70)
    print()
    print("Modelos disponibles:")
    print()

    for i, model in enumerate(provider.models, 1):
        default_mark = " (Por defecto)" if model == provider.default_model else ""
        print(f"  {i}. {model}{default_mark}")

    print()
    print(f"  0. Usar modelo por defecto ({provider.default_model})")
    print()

    while True:
        try:
            choice = input(f"Selecciona una opción (0-{len(provider.models)}): ").strip()

            if not choice or choice == "0":
                return provider.default_model

            choice_num = int(choice)

            if 1 <= choice_num <= len(provider.models):
                return provider.models[choice_num - 1]
            else:
                print(f"❌ Opción inválida. Selecciona entre 0 y {len(provider.models)}.")

        except ValueError:
            print("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            print("\n\n❌ Selección cancelada.")
            raise


def configure_azure_settings() -> Dict[str, str]:
    """
    Configura settings específicos de Azure

    Returns:
        Diccionario con configuración de Azure
    """
    print()
    print("⚙️  Configuración de Azure OpenAI")
    print("=" * 70)
    print()
    print("Para usar Azure OpenAI necesitas proporcionar:")
    print()

    endpoint = input("Azure Endpoint (ej: https://tu-recurso.openai.azure.com/): ").strip()
    deployment = input("Deployment Name: ").strip()
    api_version = input("API Version (default: 2024-06-01): ").strip() or "2024-06-01"

    return {
        "azure_endpoint": endpoint,
        "azure_deployment": deployment,
        "api_version": api_version,
    }


def get_provider_info(provider_name: str) -> ModelProvider:
    """
    Obtiene información de un proveedor

    Args:
        provider_name: Nombre del proveedor

    Returns:
        Información del proveedor
    """
    return PROVIDERS.get(provider_name, PROVIDERS["deepseek"])


def interactive_model_selection() -> tuple[str, str, str, Optional[Dict[str, str]]]:
    """
    Selección interactiva de proveedor y modelo

    Returns:
        Tupla (provider_name, base_url, model_name, extra_config)
    """
    # Seleccionar proveedor
    provider_name = show_providers_menu()
    provider = PROVIDERS[provider_name]

    # Mostrar información del proveedor
    print()
    print("=" * 70)
    print(f"✓ Proveedor seleccionado: {provider.display_name}")

    if provider.requires_api_key:
        print(f"  API Key requerida: Sí")
        print(f"  Obtener API key en: {provider.api_key_url}")
    else:
        print(f"  API Key requerida: No")

    # Seleccionar modelo
    model_name = show_models_menu(provider_name)

    print(f"✓ Modelo seleccionado: {model_name}")
    print("=" * 70)

    # Configuración extra para Azure
    extra_config = None
    if provider_name == "azure":
        extra_config = configure_azure_settings()

    base_url = provider.base_url

    return provider_name, base_url, model_name, extra_config
