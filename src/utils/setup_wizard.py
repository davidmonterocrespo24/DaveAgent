"""
Setup Wizard - Asistente interactivo para configurar DaveAgent
"""
from pathlib import Path
from typing import Optional


def print_welcome_banner():
    """Muestra banner de bienvenida para primera vez"""
    print("\n" + "=" * 70)
    print("  🎉 Bienvenido a DaveAgent - Configuración Inicial")
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
    print("DaveAgent necesita una API key para funcionar.")
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


def get_provider_choice() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Pregunta qué proveedor quiere usar con menú mejorado

    Returns:
        Tupla (provider_name, base_url, model_name) o (None, None, None) para defaults
    """
    from src.utils.model_settings import interactive_model_selection

    print()
    use_defaults = input("¿Quieres usar la configuración por defecto (DeepSeek)? (s/N): ").strip().lower()

    if use_defaults == 's' or use_defaults == 'si':
        return None, None, None

    # Usar menú interactivo completo
    try:
        provider_name, base_url, model_name, extra_config = interactive_model_selection()
        # TODO: Guardar extra_config si es necesario (Azure)
        return provider_name, base_url, model_name
    except KeyboardInterrupt:
        print("\n❌ Selección cancelada. Usando configuración por defecto.")
        return None, None, None


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
    print("  ✓ No tendrás que configurar cada vez que uses DaveAgent")
    print("  ✓ La configuración se aplica automáticamente a este directorio")
    print("  ✓ Es seguro (el archivo .daveagent/.env no se sube a Git)")
    print()

    save = input("¿Guardar en .daveagent/.env? (S/n): ").strip().lower()

    if save == 'n' or save == 'no':
        print()
        print("⚠️  Configuración NO guardada.")
        print("   Deberás configurar la API key cada vez que uses DaveAgent.")
        print()
        print("   Puedes configurarla con:")
        print(f"     daveagent --api-key \"{api_key[:10]}...\"")
        print()
        return False

    # Guardar en .daveagent/.env
    try:
        daveagent_dir = Path.cwd() / '.daveagent'
        daveagent_dir.mkdir(exist_ok=True)
        env_path = daveagent_dir / '.env'

        # Verificar si ya existe
        if env_path.exists():
            print()
            print(f"⚠️  El archivo .env ya existe en: {env_path}")
            overwrite = input("¿Sobrescribir? (s/n): ").strip().lower()
            if overwrite != 's':
                print("❌ Configuración NO guardada.")
                return False

        # Crear contenido del .env
        env_content = f"# Configuración de DaveAgent\n"
        env_content += f"# Generado automáticamente\n\n"
        env_content += f"DAVEAGENT_API_KEY={api_key}\n"

        if base_url:
            env_content += f"DAVEAGENT_BASE_URL={base_url}\n"

        if model:
            env_content += f"DAVEAGENT_MODEL={model}\n"

        # Guardar archivo
        env_path.write_text(env_content, encoding='utf-8')

        print()
        print("✅ Configuración guardada exitosamente!")
        print(f"   Archivo: {env_path}")
        print()
        print("🎉 ¡Todo listo! Ahora puedes usar DaveAgent simplemente con:")
        print("   daveagent")
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

    # Paso 2: Seleccionar proveedor y modelo
    provider_name, base_url, model = get_provider_choice()

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

    # Verificar si existe .env en el directorio .daveagent
    env_path = Path.cwd() / '.daveagent' / '.env'
    if env_path.exists():
        # Hay .env pero no tiene DAVEAGENT_API_KEY
        # Probablemente configurado mal
        return True

    # No hay API key y no hay .env
    return True
