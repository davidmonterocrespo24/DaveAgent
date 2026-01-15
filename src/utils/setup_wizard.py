"""
Setup Wizard - Asistente interactivo para configurar DaveAgent
"""

from pathlib import Path


def print_welcome_banner():
    """Shows welcome banner for first time"""
    print("\n" + "=" * 70)
    print("  🎉 Welcome to DaveAgent - Initial Setup")
    print("=" * 70)
    print()


def get_api_key_interactive() -> str:
    """
    Requests the API key interactively

    Returns:
        API key entered by the user
    """
    print("📝 API Key Configuration")
    print("-" * 70)
    print()
    print("DaveAgent needs an API key to work.")
    print()
    print("Recommended options:")
    print("  1. DeepSeek (Free) - https://platform.deepseek.com/api_keys")
    print("  2. OpenAI (GPT-4)  - https://platform.openai.com/api-keys")
    print()
    print("If you don't have an API key, you can:")
    print("  • Press Ctrl+C to cancel")
    print("  • Go to DeepSeek to create a free account")
    print()

    while True:
        api_key = input("🔑 Enter your API key: ").strip()

        if not api_key:
            print("❌ API key cannot be empty. Try again.")
            continue

        if len(api_key) < 10:
            print("❌ API key seems too short. Verify it's correct.")
            retry = input("Do you want to try again? (y/n): ").strip().lower()
            if retry != "y":
                # User doesn't want to retry, return what they entered
                return api_key
            continue

        # Basic format validation
        if not (api_key.startswith("sk-") or api_key.startswith("sess-")):
            print("⚠️  Warning: API keys usually start with 'sk-' or 'sess-'")
            confirm = input("Are you sure this key is correct? (y/n): ").strip().lower()
            if confirm != "y":
                continue

        return api_key


def get_provider_choice() -> tuple[str | None, str | None, str | None]:
    """
    Asks which provider to use with improved menu

    Returns:
        Tuple (provider_name, base_url, model_name) or (None, None, None) for defaults
    """
    from src.utils.model_settings import interactive_model_selection

    print()
    use_defaults = (
        input("Do you want to use the default configuration (DeepSeek)? (y/N): ").strip().lower()
    )

    if use_defaults == "y" or use_defaults == "yes":
        return None, None, None

    # Use complete interactive menu
    try:
        provider_name, base_url, model_name, extra_config = interactive_model_selection()
        # TODO: Save extra_config if needed (Azure)
        return provider_name, base_url, model_name
    except KeyboardInterrupt:
        print("\n❌ Selection cancelled. Using default configuration.")
        return None, None, None


def ask_save_to_env(api_key: str, base_url: str | None = None, model: str | None = None) -> bool:
    """
    Asks if they want to save the configuration to .env

    Args:
        api_key: API key to save
        base_url: Base URL (optional)
        model: Model (optional)

    Returns:
        True if saved correctly, False if not
    """
    print()
    print("💾 Save Configuration")
    print("-" * 70)
    print()
    print("Where do you want to save this configuration?")
    print()
    print("Options:")
    print("  1. User folder (GLOBAL) - Recommended")
    print("     All DaveAgent projects will use this configuration")
    print(f"     Location: {Path.home() / '.daveagent' / '.env'}")
    print()
    print("  2. Project folder (LOCAL)")
    print("     Only this project will use this configuration")
    print(f"     Location: {Path(__file__).resolve().parent.parent.parent / '.daveagent' / '.env'}")
    print()
    print("  3. Don't save")
    print()

    while True:
        choice = input("Select option (1/2/3): ").strip()
        
        if choice == "3":
            print()
            print("⚠️  Configuration NOT saved.")
            print("   You will need to configure the API key each time you use DaveAgent.")
            print()
            print("   You can configure it with:")
            print(f'     daveagent --api-key "{api_key[:10]}..."')
            print()
            return False
        
        if choice in ["1", "2"]:
            break
        
        print("❌ Invalid option. Please enter 1, 2, or 3.")

    # Determine save location
    try:
        if choice == "1":
            # Global user configuration
            daveagent_dir = Path.home() / ".daveagent"
            location_name = "user folder (GLOBAL)"
        else:
            # Local project configuration
            project_root = Path(__file__).resolve().parent.parent.parent
            daveagent_dir = project_root / ".daveagent"
            location_name = "project folder (LOCAL)"
        
        daveagent_dir.mkdir(exist_ok=True)
        env_path = daveagent_dir / ".env"

        # Check if already exists
        if env_path.exists():
            print()
            print(f"⚠️  .env file already exists at: {env_path}")
            overwrite = input("Overwrite? (y/n): ").strip().lower()
            if overwrite != "y":
                print("❌ Configuration NOT saved.")
                return False

        # Create .env content
        env_content = "# DaveAgent Configuration\n"
        env_content += f"# Generated automatically - {location_name}\n"
        env_content += "# Edit this file to change your configuration\n\n"
        env_content += f"DAVEAGENT_API_KEY={api_key}\n"

        if base_url:
            env_content += f"DAVEAGENT_BASE_URL={base_url}\n"

        if model:
            env_content += f"DAVEAGENT_MODEL={model}\n"
        
        # Add SSL configuration with default value
        env_content += "\n# SSL Configuration\n"
        env_content += "# Set to false if you have SSL certificate issues\n"
        env_content += "# DAVEAGENT_SSL_VERIFY=false\n"

        # Save file
        env_path.write_text(env_content, encoding="utf-8")

        # Reload environment variables from the saved file
        from dotenv import load_dotenv

        load_dotenv(env_path, override=True)

        print()
        print("✅ Configuration saved successfully!")
        print(f"   Location: {location_name}")
        print(f"   File: {env_path}")
        print()
        if choice == "1":
            print("🌍 This configuration will be used globally for all DaveAgent projects.")
            print("   To use a different config for a specific project, create")
            print("   a .daveagent/.env file in that project.")
        else:
            print("📁 This configuration will only be used for this project.")
            print("   To create a global configuration, run the setup again.")
        print()
        print("🎉 All set! You can now use DaveAgent simply with:")
        print("   daveagent")
        print()

        return True

    except Exception as e:
        print()
        print(f"❌ Error saving .env: {e}")
        print("   You can create the file manually.")
        return False


def run_interactive_setup() -> tuple[str, str | None, str | None]:
    """
    Runs the complete configuration wizard

    Returns:
        Tuple (api_key, base_url, model)
    """
    print_welcome_banner()

    # Step 1: Get API key
    api_key = get_api_key_interactive()

    # Step 2: Select provider and model
    provider_name, base_url, model = get_provider_choice()

    # Step 3: Ask to save
    ask_save_to_env(api_key, base_url, model)

    return api_key, base_url, model


def should_run_setup(api_key: str | None) -> bool:
    """
    Determines if interactive setup should run

    Args:
        api_key: Current API key (can be None)

    Returns:
        True if setup should run
    """
    # If already has API key, doesn't need setup
    if api_key:
        return False

    # Check if .env exists in user's home directory (global)
    user_env_path = Path.home() / ".daveagent" / ".env"
    if user_env_path.exists():
        # .env exists but doesn't have DAVEAGENT_API_KEY
        # Probably misconfigured
        return True
    
    # Check if .env exists in project directory (local)
    project_root = Path(__file__).resolve().parent.parent.parent
    project_env_path = project_root / ".daveagent" / ".env"
    if project_env_path.exists():
        # .env exists but doesn't have DAVEAGENT_API_KEY
        # Probably misconfigured
        return True

    # No API key and no .env anywhere
    return True
