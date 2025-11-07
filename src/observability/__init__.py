"""
Módulo de observabilidad con Langfuse

Este módulo proporciona integración con Langfuse para trazabilidad
y monitoreo de agentes de AutoGen.

Hay dos formas de usar Langfuse:

1. **Simple (Recomendado)**: Usando OpenLit - tracking automático
   from src.observability import init_langfuse_tracing
   init_langfuse_tracing()

2. **Avanzado**: Usando LangfuseTracker - control manual
   from src.observability import LangfuseTracker
   tracker = LangfuseTracker()
"""

from .langfuse_simple import init_langfuse_tracing, is_langfuse_enabled

# Solo exportar el método simple con OpenLit (recomendado)
__all__ = [
    "init_langfuse_tracing",      # Método simple con OpenLit (recomendado)
    "is_langfuse_enabled",         # Verificar configuración
]
