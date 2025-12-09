"""
DaveAgent Configuration - API keys and URLs management
Environment variables are loaded from .daveagent/.env
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Load environment variables from .daveagent/.env if it exists
# Priority: .daveagent/.env > .env (for compatibility)
# Search from project root (where src/ is), not from cwd
# This ensures it works even when executed from subdirectories (e.g. eval/)
project_root = Path(__file__).resolve().parent.parent.parent
daveagent_env = project_root / ".daveagent" / ".env"
legacy_env = project_root / ".env"

if daveagent_env.exists():
    load_dotenv(daveagent_env)
elif legacy_env.exists():
    load_dotenv(legacy_env)


class DaveAgentSettings:
    """Centralized DaveAgent configuration"""

    # Valores por defecto
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-reasoner"
    DEFAULT_SSL_VERIFY = True

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        ssl_verify: Optional[bool] = None,
    ):
        """
        Initializes the configuration with priority:
        1. Parameters passed directly
        2. Environment variables
        3. Default values

        Args:
            api_key: API key for the LLM model
            base_url: Base URL of the API
            model: Name of the model to use
            ssl_verify: If True, verify SSL certificates (default True)
        """
        # API Key (required)
        self.api_key = (
            api_key
            or os.getenv("DAVEAGENT_API_KEY")
            or os.getenv("CODEAGENT_API_KEY")  # Compatibility
            or os.getenv("OPENAI_API_KEY")  # Compatibility
            or os.getenv("DEEPSEEK_API_KEY")  # Compatibility
        )

        # Base URL (optional, with default value)
        self.base_url = (
            base_url
            or os.getenv("DAVEAGENT_BASE_URL")
            or os.getenv("CODEAGENT_BASE_URL")  # Compatibility
            or os.getenv("OPENAI_BASE_URL")  # Compatibility
            or self.DEFAULT_BASE_URL
        )

        # Model (optional, with default value)
        self.model = (
            model
            or os.getenv("DAVEAGENT_MODEL")
            or os.getenv("CODEAGENT_MODEL")  # Compatibility
            or os.getenv("OPENAI_MODEL")  # Compatibility
            or self.DEFAULT_MODEL
        )

        # SSL Verify (optional, with default value)
        if ssl_verify is not None:
            self.ssl_verify = ssl_verify
        else:
            # Read from environment variable (can be "true", "false", "1", "0")
            env_ssl = os.getenv("DAVEAGENT_SSL_VERIFY") or os.getenv("SSL_VERIFY")
            if env_ssl:
                self.ssl_verify = env_ssl.lower() in ("true", "1", "yes", "on")
            else:
                self.ssl_verify = self.DEFAULT_SSL_VERIFY

    def validate(self, interactive: bool = True) -> tuple[bool, Optional[str]]:
        """
        Validates that the configuration is correct

        Args:
            interactive: If True, can start interactive setup if API key is missing

        Returns:
            Tuple (is_valid, error_message)
        """
        if not self.api_key:
            if interactive:
                # Start interactive setup
                from src.utils import run_interactive_setup

                try:
                    print()
                    print("[WARNING] No API key found.")
                    print()
                    response = (
                        input("Do you want to configure DaveAgent now? (Y/n): ").strip().lower()
                    )

                    if response == "n" or response == "no":
                        return False, (
                            "[ERROR] API key not configured.\n\n"
                            "Options to configure it:\n"
                            "  1. Environment variable: export DAVEAGENT_API_KEY='your-api-key'\n"
                            "  2. File .daveagent/.env: DAVEAGENT_API_KEY=your-api-key\n"
                            "  3. CLI argument: daveagent --api-key 'your-api-key'\n\n"
                            "Get your API key at: https://platform.deepseek.com/api_keys"
                        )

                    # Execute interactive setup
                    api_key, base_url, model = run_interactive_setup()

                    # Update configuration
                    self.api_key = api_key
                    if base_url:
                        self.base_url = base_url
                    if model:
                        self.model = model

                    # Validate again (without interactivity to avoid loop)
                    return self.validate(interactive=False)

                except KeyboardInterrupt:
                    print("\n\n[ERROR] Configuration cancelled by user.")
                    return False, "Configuration cancelled"
                except Exception as e:
                    print(f"\n[ERROR] Error during configuration: {e}")
                    return False, f"Configuration error: {e}"
            else:
                return False, (
                    "[ERROR] API key not configured.\n\n"
                    "Options to configure it:\n"
                    "  1. Environment variable: export DAVEAGENT_API_KEY='your-api-key'\n"
                    "  2. File .daveagent/.env: DAVEAGENT_API_KEY=your-api-key\n"
                    "  3. CLI argument: daveagent --api-key 'your-api-key'\n\n"
                    "Get your API key at: https://platform.deepseek.com/api_keys"
                )

        if not self.base_url:
            return False, "[ERROR] Base URL not configured"

        if not self.model:
            return False, "[ERROR] Model not configured"

        return True, None

    def get_model_capabilities(self) -> dict:
        """
        Gets the model's capabilities according to the base URL

        Returns:
            Dictionary with model capabilities
        """
        # Capabilities for DeepSeek
        if "deepseek" in self.base_url.lower():
            return {
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": False,
            }

        # Capabilities for OpenAI
        if "openai" in self.base_url.lower():
            return {
                "vision": True,  # GPT-4 Vision
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
            }

        # Generic capabilities by default
        return {
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }

    def __repr__(self) -> str:
        """String representation (hiding API key)"""
        masked_key = (
            f"{self.api_key[:8]}...{self.api_key[-4:]}" if self.api_key else "Not configured"
        )
        return (
            f"DaveAgentSettings(\n"
            f"  api_key={masked_key},\n"
            f"  base_url={self.base_url},\n"
            f"  model={self.model},\n"
            f"  ssl_verify={self.ssl_verify}\n"
            f")"
        )


def get_settings(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    ssl_verify: Optional[bool] = None,
) -> DaveAgentSettings:
    """
    Factory function to get configuration

    Args:
        api_key: API key (optional)
        base_url: Base URL (optional)
        model: Model name (optional)
        ssl_verify: Whether to verify SSL (optional)

    Returns:
        DaveAgentSettings instance
    """
    return DaveAgentSettings(api_key=api_key, base_url=base_url, model=model, ssl_verify=ssl_verify)


# Maintain compatibility with old code
CodeAgentSettings = DaveAgentSettings
