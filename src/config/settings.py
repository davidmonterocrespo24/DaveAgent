"""
Configuración de DaveAgent - Manejo de API keys y URLs
Variables de entorno se cargan desde .daveagent/.env
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .daveagent/.env si existe
# Prioridad: .daveagent/.env > .env (para compatibilidad)
daveagent_env = Path.cwd() / '.daveagent' / '.env'
legacy_env = Path.cwd() / '.env'

if daveagent_env.exists():
    load_dotenv(daveagent_env)
elif legacy_env.exists():
    load_dotenv(legacy_env)


class DaveAgentSettings:
    """Configuración centralizada de DaveAgent"""

    # Valores por defecto
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-reasoner"
    DEFAULT_SSL_VERIFY = True

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        ssl_verify: Optional[bool] = None
    ):
        """
        Inicializa la configuración con prioridad:
        1. Parámetros pasados directamente
        2. Variables de entorno
        3. Valores por defecto

        Args:
            api_key: API key para el modelo LLM
            base_url: URL base de la API
            model: Nombre del modelo a usar
            ssl_verify: Si True, verifica certificados SSL (por defecto True)
        """
        # API Key (requerida)
        self.api_key = (
            api_key
            or os.getenv("DAVEAGENT_API_KEY")
            or os.getenv("CODEAGENT_API_KEY")  # Compatibilidad
            or os.getenv("OPENAI_API_KEY")  # Compatibilidad
            or os.getenv("DEEPSEEK_API_KEY")  # Compatibilidad
        )

        # Base URL (opcional, con valor por defecto)
        self.base_url = (
            base_url
            or os.getenv("DAVEAGENT_BASE_URL")
            or os.getenv("CODEAGENT_BASE_URL")  # Compatibilidad
            or os.getenv("OPENAI_BASE_URL")  # Compatibilidad
            or self.DEFAULT_BASE_URL
        )

        # Modelo (opcional, con valor por defecto)
        self.model = (
            model
            or os.getenv("DAVEAGENT_MODEL")
            or os.getenv("CODEAGENT_MODEL")  # Compatibilidad
            or os.getenv("OPENAI_MODEL")  # Compatibilidad
            or self.DEFAULT_MODEL
        )

        # SSL Verify (opcional, con valor por defecto)
        if ssl_verify is not None:
            self.ssl_verify = ssl_verify
        else:
            # Leer de variable de entorno (puede ser "true", "false", "1", "0")
            env_ssl = (
                os.getenv("DAVEAGENT_SSL_VERIFY") 
                or os.getenv("SSL_VERIFY")
            )
            if env_ssl:
                self.ssl_verify = env_ssl.lower() in ("true", "1", "yes", "on")
            else:
                self.ssl_verify = self.DEFAULT_SSL_VERIFY

    def validate(self, interactive: bool = True) -> tuple[bool, Optional[str]]:
        """
        Valida que la configuración sea correcta

        Args:
            interactive: Si True, puede iniciar setup interactivo si falta API key

        Returns:
            Tupla (is_valid, error_message)
        """
        if not self.api_key:
            if interactive:
                # Iniciar setup interactivo
                from src.utils import run_interactive_setup

                try:
                    print()
                    print("[WARNING] No se encontro una API key configurada.")
                    print()
                    response = input("Quieres configurar DaveAgent ahora? (S/n): ").strip().lower()

                    if response == 'n' or response == 'no':
                        return False, (
                            "[ERROR] API key no configurada.\n\n"
                            "Opciones para configurarla:\n"
                            "  1. Variable de entorno: export DAVEAGENT_API_KEY='tu-api-key'\n"
                            "  2. Archivo .daveagent/.env: DAVEAGENT_API_KEY=tu-api-key\n"
                            "  3. Argumento CLI: daveagent --api-key 'tu-api-key'\n\n"
                            "Obtén tu API key en: https://platform.deepseek.com/api_keys"
                        )

                    # Ejecutar setup interactivo
                    api_key, base_url, model = run_interactive_setup()

                    # Actualizar configuración
                    self.api_key = api_key
                    if base_url:
                        self.base_url = base_url
                    if model:
                        self.model = model

                    # Validar de nuevo (sin interactividad para evitar loop)
                    return self.validate(interactive=False)

                except KeyboardInterrupt:
                    print("\n\n[ERROR] Configuracion cancelada por el usuario.")
                    return False, "Configuracion cancelada"
                except Exception as e:
                    print(f"\n[ERROR] Error durante la configuracion: {e}")
                    return False, f"Error en configuración: {e}"
            else:
                return False, (
                    "[ERROR] API key no configurada.\n\n"
                    "Opciones para configurarla:\n"
                    "  1. Variable de entorno: export DAVEAGENT_API_KEY='tu-api-key'\n"
                    "  2. Archivo .daveagent/.env: DAVEAGENT_API_KEY=tu-api-key\n"
                    "  3. Argumento CLI: daveagent --api-key 'tu-api-key'\n\n"
                    "Obten tu API key en: https://platform.deepseek.com/api_keys"
                )

        if not self.base_url:
            return False, "[ERROR] Base URL no configurada"

        if not self.model:
            return False, "[ERROR] Modelo no configurado"

        return True, None

    def get_model_capabilities(self) -> dict:
        """
        Obtiene las capacidades del modelo según la base URL

        Returns:
            Diccionario con capacidades del modelo
        """
        # Capacidades para DeepSeek
        if "deepseek" in self.base_url.lower():
            return {
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": False,
            }

        # Capacidades para OpenAI
        if "openai" in self.base_url.lower():
            return {
                "vision": True,  # GPT-4 Vision
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
            }

        # Capacidades genéricas por defecto
        return {
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }

    def __repr__(self) -> str:
        """Representación en string (ocultando API key)"""
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if self.api_key else "No configurada"
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
    ssl_verify: Optional[bool] = None
) -> DaveAgentSettings:
    """
    Factory function para obtener configuración

    Args:
        api_key: API key (opcional)
        base_url: URL base (opcional)
        model: Nombre del modelo (opcional)
        ssl_verify: Si verificar SSL (opcional)

    Returns:
        Instancia de DaveAgentSettings
    """
    return DaveAgentSettings(api_key=api_key, base_url=base_url, model=model, ssl_verify=ssl_verify)


# Mantener compatibilidad con código antiguo
CodeAgentSettings = DaveAgentSettings
