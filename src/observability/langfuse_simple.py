"""
Integración simplificada de Langfuse con AutoGen usando OpenLit

Esta es la forma oficial y recomendada de integrar Langfuse con AutoGen.
OpenLit captura automáticamente todas las operaciones de AutoGen.
"""

import os
from typing import Optional


def init_langfuse_tracing(
    enabled: bool = True,
    debug: bool = False
) -> bool:
    """
    Inicializa el tracing de Langfuse usando OpenLit (método oficial)

    Esta función configura automáticamente el tracing de todas las operaciones
    de AutoGen sin necesidad de modificar código adicional.

    Args:
        enabled: Si False, no se inicializa el tracing
        debug: Si True, imprime información de debug

    Returns:
        True si se inicializó correctamente, False en caso contrario

    Ejemplo:
        >>> from src.observability.langfuse_simple import init_langfuse_tracing
        >>> init_langfuse_tracing()
        True
    """
    if not enabled:
        if debug:
            print("[INFO] Langfuse tracing deshabilitado")
        return False

    try:
        # Verificar que las variables de entorno estén configuradas
        required_vars = [
            "LANGFUSE_SECRET_KEY",
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_HOST"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            if debug:
                print(f"[WARNING] Variables de entorno faltantes: {', '.join(missing_vars)}")
                print("[INFO] Langfuse tracing no se inicializará")
            return False

        # Importar Langfuse y OpenLit
        from langfuse import Langfuse
        import openlit

        if debug:
            print("[INFO] Inicializando Langfuse client...")

        # Inicializar cliente Langfuse
        langfuse = Langfuse()

        # Verificar autenticación
        if not langfuse.auth_check():
            if debug:
                print("[ERROR] Autenticación con Langfuse falló")
            return False

        if debug:
            print("[OK] Langfuse client autenticado")
            print("[INFO] Inicializando OpenLit instrumentation...")

        # Inicializar OpenLit con el tracer de Langfuse
        # OpenLit capturará automáticamente todas las operaciones de AutoGen
        openlit.init(
            tracer=langfuse._otel_tracer,
            disable_batch=True  # Procesar trazas inmediatamente
        )

        if debug:
            print("[OK] OpenLit instrumentation inicializada")
            print("[OK] Langfuse tracing activo - todas las operaciones de AutoGen serán trackeadas")

        return True

    except ImportError as e:
        if debug:
            print(f"[ERROR] Error importando dependencias: {e}")
            print("[INFO] Instala: pip install langfuse openlit")
        return False

    except Exception as e:
        if debug:
            print(f"[ERROR] Error inicializando Langfuse: {e}")
        return False


def is_langfuse_enabled() -> bool:
    """
    Verifica si Langfuse está habilitado y configurado

    Returns:
        True si las variables de entorno están configuradas
    """
    required_vars = [
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_HOST"
    ]

    return all(os.getenv(var) for var in required_vars)


# Inicialización automática al importar el módulo (opcional)
# Puedes comentar estas líneas si prefieres inicializar manualmente
if __name__ != "__main__":
    # Solo inicializar si no estamos ejecutando este archivo directamente
    pass  # No auto-inicializar, esperar a que main.py lo haga explícitamente
