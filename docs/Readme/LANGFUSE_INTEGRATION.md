# Integración de Langfuse con DaveAgent

## 📋 Descripción

Langfuse es una plataforma de observabilidad LLM de código abierto que proporciona trazabilidad completa de las llamadas al modelo, métricas de rendimiento y análisis de costos.

Esta integración permite rastrear todas las interacciones con el LLM en DaveAgent, incluyendo:
- Llamadas individuales al modelo
- Conversaciones multi-agente
- Uso de herramientas (function calling)
- Tokens consumidos
- Latencia de respuesta
- Costos estimados

## 🚀 Instalación

Las dependencias ya están instaladas:

```bash
pip install langfuse openlit
```

## ⚙️ Configuración

### 1. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```properties
# Langfuse Configuration
LANGFUSE_SECRET_KEY=sk-lf-64bbd984-0edb-45c8-bd0a-77e0b65fed2d
LANGFUSE_PUBLIC_KEY=pk-lf-12d38bdc-d425-4b8f-9b0e-86e9ae6982e6
LANGFUSE_HOST=https://langfuse-u0sg0c8gokgkwwk084844k8o.daveplanet.com
```

### 2. Código de Inicialización

```python
import os
from dotenv import load_dotenv
from langfuse import Langfuse
import openlit

# Cargar variables de entorno
load_dotenv()

# Inicializar Langfuse
langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
    blocked_instrumentation_scopes=["autogen SingleThreadedAgentRuntime"]
)

# Verificar autenticación
if langfuse.auth_check():
    print("✅ Langfuse autenticado correctamente")

# Inicializar OpenLit para instrumentación automática
openlit.init(tracer=langfuse._otel_tracer, disable_batch=True)
```

## 🧪 Tests

Se han creado 3 suites de tests para verificar la integración:

### Test 1: Básico (`test_langfuse_basic.py`)

Verifica:
- ✅ Autenticación con Langfuse
- ✅ Creación de trazas simples
- ✅ Conexión al servidor

**Ejecutar:**
```bash
python test/test_langfuse_basic.py
```

### Test 2: Integración AutoGen (`test_langfuse_autogen_integration.py`)

Verifica:
- ✅ OpenLit + AutoGen funcionando juntos
- ✅ Trazas de llamadas al LLM capturadas
- ✅ Metadata correcta en las trazas

**Ejecutar:**
```bash
python test/test_langfuse_autogen_integration.py
```

### Test 3: Multi-Agente (`test_langfuse_multi_agent.py`)

Verifica:
- ✅ Conversaciones multi-agente rastreadas
- ✅ Trazas de múltiples agentes organizadas
- ✅ Herramientas (function calling) rastreadas

**Ejecutar:**
```bash
python test/test_langfuse_multi_agent.py
```

### Ejecutar todos los tests

```bash
python test/run_langfuse_tests.py
```

## 📊 Dashboard de Langfuse

Accede a tu dashboard para ver las trazas:

🔗 **URL:** https://langfuse-u0sg0c8gokgkwwk084844k8o.daveplanet.com

### Qué verás en el dashboard:

1. **Trazas (Traces):**
   - Cada conversación completa
   - Flujo de mensajes entre agentes
   - Llamadas al LLM con contexto completo

2. **Métricas:**
   - Tokens consumidos (prompt + completion)
   - Latencia de cada llamada
   - Costo estimado por llamada
   - Tasa de éxito/error

3. **Agentes:**
   - Identificación de cada agente (Coder, Planner, etc.)
   - Trazas agrupadas por agente
   - Rendimiento por agente

4. **Herramientas:**
   - Llamadas a function calling
   - Parámetros enviados
   - Resultados obtenidos

## 🔧 Integración con main.py

Para integrar Langfuse en `main.py`, agrega esto al inicio de la clase `DaveAgentCLI.__init__`:

```python
def __init__(self, debug: bool = False, ...):
    # ... código existente ...
    
    # Inicializar Langfuse (DESPUÉS de cargar settings)
    self.logger.info("📊 Inicializando Langfuse para observabilidad...")
    
    from langfuse import Langfuse
    import openlit
    
    self.langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
        blocked_instrumentation_scopes=["autogen SingleThreadedAgentRuntime"]
    )
    
    if self.langfuse.auth_check():
        self.logger.info("✅ Langfuse autenticado correctamente")
        
        # Inicializar OpenLit
        openlit.init(tracer=self.langfuse._otel_tracer, disable_batch=True)
        self.logger.info("✅ OpenLit instrumentación activada")
    else:
        self.logger.warning("⚠️ Langfuse no pudo autenticarse")
    
    # ... resto del código ...
```

Y en el método `close()` o al final de `run()`:

```python
# Flush Langfuse antes de cerrar
if hasattr(self, 'langfuse'):
    self.langfuse.flush()
    self.logger.info("✅ Trazas de Langfuse enviadas")
```

## 📈 Beneficios

### 1. **Observabilidad Completa**
- Visualiza todas las llamadas al LLM en tiempo real
- Entiende el flujo de conversaciones complejas
- Identifica cuellos de botella

### 2. **Análisis de Costos**
- Monitorea tokens consumidos
- Calcula costos por sesión
- Optimiza uso del modelo

### 3. **Debugging**
- Rastrea errores en llamadas al LLM
- Revisa prompts exactos enviados
- Analiza respuestas del modelo

### 4. **Mejora Continua**
- Compara rendimiento entre sesiones
- Identifica patrones de uso
- Optimiza system messages

## 🎯 Próximos Pasos

1. ✅ Ejecutar los tests para verificar funcionamiento
2. ⏳ Integrar Langfuse en `main.py`
3. ⏳ Configurar alertas en dashboard
4. ⏳ Crear dashboards personalizados
5. ⏳ Configurar límites de costos

## 🔗 Enlaces Útiles

- **Dashboard:** https://langfuse-u0sg0c8gokgkwwk084844k8o.daveplanet.com
- **Documentación Langfuse:** https://langfuse.com/docs
- **Documentación OpenLit:** https://github.com/openlit/openlit
- **AutoGen + Langfuse:** https://langfuse.com/docs/integrations/autogen

## ❓ Troubleshooting

### Error: "Authentication failed"

Verifica que las keys en `.env` sean correctas:
```bash
cat .env | grep LANGFUSE
```

### Error: "Cannot connect to host"

Verifica que el host sea accesible:
```bash
curl https://langfuse-u0sg0c8gokgkwwk084844k8o.daveplanet.com/api/public/health
```

### No aparecen trazas en el dashboard

1. Verifica que `openlit.init()` se llame ANTES de crear agentes
2. Asegúrate de llamar `langfuse.flush()` al final
3. Revisa los logs del test para errores

## 📝 Notas

- Las trazas se envían en tiempo real (disable_batch=True)
- Langfuse filtra spans de AutoGen runtime (evita ruido)
- Los tests usan DeepSeek como modelo (configurable)
- Las trazas se almacenan por 30 días (plan gratuito)
