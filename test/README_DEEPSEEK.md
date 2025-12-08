# Test de DeepSeek-Reasoner con AutoGen 0.4

Este ejemplo demuestra cómo integrar **DeepSeek-R1 (deepseek-reasoner)** con **Microsoft AutoGen 0.4**.

## ¿Qué es DeepSeek-Reasoner?

DeepSeek-R1 es un modelo de IA especializado en **razonamiento lógico avanzado**. A diferencia de los modelos tradicionales, DeepSeek-Reasoner:

- ✅ Muestra su **proceso de pensamiento** antes de responder
- ✅ Analiza problemas **paso a paso**
- ✅ Es excelente para **matemáticas, lógica y razonamiento**
- ✅ **SÍ soporta** function_calling (herramientas) ⚡ **VERIFICADO**
- ✅ **SÍ soporta** structured_output (JSON) ⚡ **VERIFICADO**

### ⚠️ Nota Importante sobre Capacidades

**DESCUBRIMIENTO IMPORTANTE**: Contrario a la documentación antigua, **hemos verificado mediante tests reales** que `deepseek-reasoner` SÍ soporta:
- ✅ Function calling (llamada a funciones/herramientas)
- ✅ JSON estructurado
- ✅ ReAct pattern para agentes

La documentación oficial más antigua indica que estas características no están soportadas, pero los tests con la API actual (2025) demuestran que **funcionan perfectamente**.

Ver [test_deepseek_capabilities.py](test_deepseek_capabilities.py) para pruebas detalladas.

## Compatibilidad con AutoGen

| Característica | Estado | Notas |
|----------------|--------|-------|
| AssistantAgent | ✅ Compatible | Funciona perfectamente |
| RoundRobinGroupChat | ✅ Compatible | Conversaciones multi-agente funcionan |
| SelectorGroupChat | ✅ Compatible | Selección dinámica de agentes funciona |
| Function Calling | ✅ **SOPORTADO** | **VERIFICADO** - Funciona con `function_calling=True` |
| Structured Output | ✅ **SOPORTADO** | **VERIFICADO** - Puede generar JSON válido |
| Herramientas (Tools) | ✅ **SOPORTADO** | **VERIFICADO** - Puede usar herramientas de AutoGen |

## Configuración

### 1. Obtener API Key de DeepSeek

1. Visita [https://platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
2. Crea una cuenta o inicia sesión
3. Genera una nueva API key

### 2. Configurar el .env

Agrega tu API key al archivo `.env` en la raíz del proyecto:

```env
DAVEAGENT_API_KEY=sk-tu-api-key-aqui
CODEAGENT_API_KEY=sk-tu-api-key-aqui  # Compatibility
```

## Tests Disponibles

### Test Básico: test_deepseek_reasoner.py

Script con 4 ejemplos de razonamiento:

```bash
python test/test_deepseek_reasoner.py
```

1. **Razonamiento Matemático Simple** ⚡ (rápido)
2. **Problema de Lógica** 🧩 (medio)
3. **Conversación Multi-Agente** 👥 (medio)
4. **Razonamiento sobre Código** 💻 (medio)

### Test de Capacidades: test_deepseek_capabilities.py

Script que **VERIFICA** las capacidades reales del modelo:

```bash
python test/test_deepseek_capabilities.py
```

Este test demuestra:
- ✅ Function calling funciona con `function_calling=True`
- ✅ JSON estructurado funciona con `json_output=True`
- ✅ JSON via prompt engineering también funciona
- ✅ ReAct pattern para simular herramientas funciona

## Ejemplo de Salida - Function Calling

```
================================================================================
TEST 1: Function Calling HABILITADO (function_calling=True)
================================================================================

Pregunta: Cual es el clima en Madrid?
Ejecutando con function_calling=True...

--- RESULTADO ---

[weather_agent]: Te ayudo a consultar el clima en Madrid.

[weather_agent]: [FunctionCall(id='call_00_...', arguments='{"city": "Madrid"}',
                              name='get_weather')]

[weather_agent]: [FunctionExecutionResult(content='El clima en Madrid es soleado, 25 grados',
                                        name='get_weather', call_id='call_00_...')]

[weather_agent]: El clima en Madrid es soleado, 25 grados

✅ EXITO: DeepSeek-Reasoner PUEDE usar function calling!
```

## Ejemplo de Salida - JSON Estructurado

```
================================================================================
TEST 2: JSON Output HABILITADO (json_output=True)
================================================================================

Pregunta: Dame informacion sobre Python en formato JSON

--- RESULTADO ---

[json_agent]: {
  "nombre": "Python",
  "tipo": "Lenguaje de programación",
  "año_creacion": 1991
}

✅ EXITO: La respuesta es JSON valido!
```

## Código de Ejemplo

### Agente con Function Calling

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Configurar cliente CON function calling
client = OpenAIChatCompletionClient(
    model="deepseek-reasoner",
    api_key="tu-api-key",
    base_url="https://api.deepseek.com",
    model_capabilities={
        "function_calling": True,  # ✅ HABILITAR
        "json_output": True,       # ✅ HABILITAR
        "vision": False,
        "structured_output": True,
    }
)

# Definir herramienta
async def get_weather(city: str) -> str:
    """Obtiene el clima de una ciudad"""
    return f"El clima en {city} es soleado, 25 grados"

# Crear agente con herramienta
agent = AssistantAgent(
    name="weather_agent",
    model_client=client,
    tools=[get_weather],  # ✅ Agregar herramientas
    system_message="Eres un asistente que puede consultar el clima.",
)

# Usar agente
result = await agent.run(task="¿Cuál es el clima en Madrid?")
```

### Agente con JSON Estructurado

```python
# Cliente con JSON habilitado
client = OpenAIChatCompletionClient(
    model="deepseek-reasoner",
    api_key="tu-api-key",
    base_url="https://api.deepseek.com",
    model_capabilities={
        "function_calling": False,
        "json_output": True,        # ✅ HABILITAR JSON
        "structured_output": True,
    }
)

agent = AssistantAgent(
    name="json_agent",
    model_client=client,
    system_message="Responde en formato JSON válido.",
)

result = await agent.run(
    task="Dame info sobre Python en JSON con campos: nombre, tipo, año_creacion"
)
```

### Multi-Agente con Tools

```python
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

# Crear agentes con herramientas
agent1 = AssistantAgent(
    name="researcher",
    model_client=client,
    tools=[search_web, read_file],  # ✅ Con herramientas
)

agent2 = AssistantAgent(
    name="writer",
    model_client=client,
    tools=[write_file],  # ✅ Con herramientas
)

# Crear equipo
team = RoundRobinGroupChat(
    participants=[agent1, agent2],
    termination_condition=TextMentionTermination("TERMINATE"),
)

result = await team.run(task="Investiga sobre IA y escribe un resumen")
```

## Comparación: deepseek-reasoner vs deepseek-chat

| Característica | deepseek-reasoner | deepseek-chat |
|----------------|-------------------|---------------|
| Razonamiento avanzado | ✅ Excelente | ⚠️ Bueno |
| Muestra proceso de pensamiento | ✅ Sí | ❌ No |
| Function calling | ✅ **Sí** | ✅ Sí |
| Structured output (JSON) | ✅ **Sí** | ✅ Sí |
| Velocidad | ⚠️ Más lento | ✅ Rápido |
| Costo | ⚠️ Más caro | ✅ Económico |

**Recomendación Actualizada**:
- Usa `deepseek-reasoner` para **problemas complejos** que requieren razonamiento profundo **Y** ahora también puedes usar herramientas
- Usa `deepseek-chat` para **tareas simples y rápidas** donde no necesitas ver el proceso de razonamiento

## Casos de Uso Ideales

DeepSeek-Reasoner es perfecto para:

1. **Agentes con Razonamiento + Herramientas** 🆕
   - Análisis complejo que requiere consultar APIs
   - Decisiones basadas en datos externos
   - Debugging con acceso a archivos

2. **Problemas Matemáticos con Verificación** 🆕
   - Resolver y verificar con calculadora
   - Análisis estadístico con datos reales

3. **Análisis de Código con Tools** 🆕
   - Leer archivos, analizar y generar reportes JSON
   - Ejecutar tests y razonar sobre resultados

4. **Planificación Multi-Agente** 🆕
   - Equipos de agentes que razonan y usan herramientas
   - Workflows complejos con decisiones informadas

5. **Debugging Conceptual con Contexto**
   - Razonar sobre errores mientras lee logs
   - Identificar problemas consultando documentación

## Limitaciones y Consideraciones

### ⚠️ Velocidad

DeepSeek-Reasoner es **más lento** que deepseek-chat porque:
- Genera razonamiento interno antes de responder
- El proceso de pensamiento puede tomar 30-60 segundos

**Solución**: Usa para tareas complejas donde el razonamiento profundo vale la pena.

### ⚠️ Costo

El modelo de razonamiento es **más costoso** debido a:
- Genera más tokens (reasoning_content + respuesta)
- Toma más tiempo de cómputo

**Solución**: Reserva para problemas que realmente lo necesiten.

### ⚠️ Documentación Desactualizada

La documentación oficial puede estar desactualizada. **SIEMPRE verifica con tests reales**.

## Troubleshooting

### Error: "API key not configured"

```bash
# Verifica que .env tenga:
DAVEAGENT_API_KEY=sk-...
# o para compatibilidad:
CODEAGENT_API_KEY=sk-...
```

### Error: Timeout

DeepSeek-Reasoner toma tiempo. Aumenta timeout:

```python
result = await agent.run(task="...", timeout=180)  # 3 minutos
```

### Error de Encoding en Windows

Si ves errores de Unicode:

```python
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
```

### Verificar Capacidades

Ejecuta el test de capacidades:

```bash
python test/test_deepseek_capabilities.py
```

Esto te mostrará qué funciona realmente en tu configuración.

## Recursos Adicionales

- [DeepSeek Platform](https://platform.deepseek.com)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [DeepSeek-R1 Paper](https://github.com/deepseek-ai/DeepSeek-R1)
- [Test de Capacidades](test_deepseek_capabilities.py) - Verifica funcionalidades reales

## Conclusión

**DeepSeek-Reasoner es mucho más capaz de lo que la documentación antigua sugiere**. Nuestros tests demuestran que:

✅ Soporta function calling completamente
✅ Soporta JSON estructurado
✅ Funciona excelente con herramientas de AutoGen
✅ Puede usarse en agentes complejos con múltiples herramientas

**No te limites por documentación desactualizada** - prueba las capacidades reales del modelo.

## Licencia

Este código de ejemplo es parte del proyecto DaveAgent y se distribuye bajo la misma licencia del proyecto principal.
