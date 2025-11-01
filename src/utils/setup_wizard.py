"""
Setup Wizard - Asistente interactivo para configurar CodeAgent
"""
from pathlib import Path
from typing import Optional


def print_welcome_banner():
    """Muestra banner de bienvenida para primera vez"""
    print("\n" + "=" * 70)
    print("  🎉 Bienvenido a CodeAgent - Configuración Inicial")
    print("=" * 70)
    print()


def get_api_key_interactive() -> str:
    """
    Solicita la API key de forma interactiva

    Returns:
        API key ingresada por el usuario
    """
    print("📝 Configuración de API Key")
    print("-" * 70)
    print()
    print("CodeAgent necesita una API key para funcionar.")
    print()
    print("Opciones recomendadas:")
    print("  1. DeepSeek (Gratis) - https://platform.deepseek.com/api_keys")
    print("  2. OpenAI (GPT-4)    - https://platform.openai.com/api-keys")
    print()
    print("Si no tienes una API key, puedes:")
    print("  • Presiona Ctrl+C para cancelar")
    print("  • Ve a DeepSeek para crear una cuenta gratis")
    print()

    while True:
        api_key = input("🔑 Ingresa tu API key: ").strip()

        if not api_key:
            print("❌ La API key no puede estar vacía. Intenta de nuevo.")
            continue

        if len(api_key) < 10:
            print("❌ La API key parece muy corta. Verifica que sea correcta.")
            retry = input("¿Quieres intentar de nuevo? (s/n): ").strip().lower()
            if retry != 's':
                break
            continue

        # Validación básica del formato
        if not (api_key.startswith('sk-') or api_key.startswith('sess-')):
            print("⚠️  Advertencia: Las API keys suelen empezar con 'sk-' o 'sess-'")
            confirm = input("¿Estás seguro de que esta key es correcta? (s/n): ").strip().lower()
            if confirm != 's':
                continue

        return api_key


def get_provider_choice() -> tuple[Optional[str], Optional[str]]:
    """
    Pregunta qué proveedor quiere usar

    Returns:
        Tupla (base_url, model_name) o (None, None) para usar defaults
    """
    print()
    print("🌐 Selección de Proveedor")
    print("-" * 70)
    print()
    print("¿Qué proveedor de IA quieres usar?")
    print()
    print("  1. DeepSeek (Recomendado - Rápido y económico)")
    print("  2. OpenAI (GPT-4 - Más potente pero costoso)")
    print("  3. Personalizado (Otra API compatible con OpenAI)")
    print("  4. Usar configuración por defecto (DeepSeek)")
    print()

    while True:
        choice = input("Selecciona una opción (1-4): ").strip()

        if choice == "1":
            return "https://api.deepseek.com", "deepseek-chat"

        elif choice == "2":
            return "https://api.openai.com/v1", "gpt-4"

        elif choice == "3":
            print()
            base_url = input("URL base de la API: ").strip()
            model = input("Nombre del modelo: ").strip()
            if base_url and model:
                return base_url, model
            else:
                print("❌ Debes ingresar ambos valores.")
                continue

        elif choice == "4" or choice == "":
            return None, None

        else:
            print("❌ Opción inválida. Selecciona 1, 2, 3 o 4.")


def ask_save_to_env(api_key: str, base_url: Optional[str] = None, model: Optional[str] = None) -> bool:
    """
    Pregunta si quiere guardar la configuración en .env

    Args:
        api_key: API key a guardar
        base_url: URL base (opcional)
        model: Modelo (opcional)

    Returns:
        True si se guardó correctamente, False si no
    """
    print()
    print("💾 Guardar Configuración")
    print("-" * 70)
    print()
    print("¿Quieres guardar esta configuración en un archivo .env?")
    print()
    print("Ventajas:")
    print("  ✓ No tendrás que configurar cada vez que uses CodeAgent")
    print("  ✓ La configuración se aplica automáticamente a este directorio")
    print("  ✓ Es seguro (el archivo .env no se sube a Git)")
    print()

    save = input("¿Guardar en .env? (S/n): ").strip().lower()

    if save == 'n' or save == 'no':
        print()
        print("⚠️  Configuración NO guardada.")
        print("   Deberás configurar la API key cada vez que uses CodeAgent.")
        print()
        print("   Puedes configurarla con:")
        print(f"     codeagent --api-key \"{api_key[:10]}...\"")
        print()
        return False

    # Guardar en .env
    try:
        env_path = Path.cwd() / '.env'

        # Verificar si ya existe
        if env_path.exists():
            print()
            print(f"⚠️  El archivo .env ya existe en: {env_path}")
            overwrite = input("¿Sobrescribir? (s/n): ").strip().lower()
            if overwrite != 's':
                print("❌ Configuración NO guardada.")
                return False

        # Crear contenido del .env
        env_content = f"# Configuración de CodeAgent\n"
        env_content += f"# Generado automáticamente\n\n"
        env_content += f"CODEAGENT_API_KEY={api_key}\n"

        if base_url:
            env_content += f"CODEAGENT_BASE_URL={base_url}\n"

        if model:
            env_content += f"CODEAGENT_MODEL={model}\n"

        # Guardar archivo
        env_path.write_text(env_content, encoding='utf-8')

        print()
        print("✅ Configuración guardada exitosamente!")
        print(f"   Archivo: {env_path}")
        print()
        print("🎉 ¡Todo listo! Ahora puedes usar CodeAgent simplemente con:")
        print("   codeagent")
        print()

        return True

    except Exception as e:
        print()
        print(f"❌ Error al guardar .env: {e}")
        print("   Puedes crear el archivo manualmente.")
        return False


def run_interactive_setup() -> tuple[str, Optional[str], Optional[str]]:
    """
    Ejecuta el asistente de configuración completo

    Returns:
        Tupla (api_key, base_url, model)
    """
    print_welcome_banner()

    # Paso 1: Obtener API key
    api_key = get_api_key_interactive()

    # Paso 2: Seleccionar proveedor
    base_url, model = get_provider_choice()

    # Paso 3: Preguntar si guardar
    ask_save_to_env(api_key, base_url, model)

    return api_key, base_url, model


def should_run_setup(api_key: Optional[str]) -> bool:
    """
    Determina si se debe ejecutar el setup interactivo

    Args:
        api_key: API key actual (puede ser None)

    Returns:
        True si se debe ejecutar el setup
    """
    # Si ya tiene API key, no necesita setup
    if api_key:
        return False

    # Verificar si existe .env en el directorio actual
    env_path = Path.cwd() / '.env'
    if env_path.exists():
        # Hay .env pero no tiene CODEAGENT_API_KEY
        # Probablemente configurado mal
        return True

    # No hay API key y no hay .env
    return True
