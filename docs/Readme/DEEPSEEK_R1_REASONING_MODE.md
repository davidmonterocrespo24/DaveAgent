# 🧠 DeepSeek R1 - Modo de Razonamiento con AutoGen

## ✅ SOLUCIÓN COMPLETAMENTE IMPLEMENTADA

**DeepSeek R1 (Reasoner) con thinking mode ahora funciona PERFECTAMENTE con tool calls y AutoGen!**

Hemos implementado `DeepSeekReasoningClient` que maneja correctamente el campo `reasoning_content` requerido por la API de DeepSeek.

---

## 🚀 Uso Rápido

### Configuración Automática

Simplemente configura tu modelo en `.daveagent/.env`:

```bash
# Para usar DeepSeek R1 con razonamiento extendido
DAVEAGENT_MODEL=deepseek-reasoner

# O usa deepseek-chat (también soportado)
DAVEAGENT_MODEL=deepseek-chat
```

**¡Eso es todo!** El sistema detecta automáticamente y habilita el modo de razonamiento.

### Al Iniciar

Verás este mensaje cuando uses DeepSeek Reasoner:

```
═══════════════════════════════════════════════════════════════
🧠 DEEPSEEK REASONER (R1) - THINKING MODE ENABLED

Este cliente usa DeepSeek R1 con modo de razonamiento extendido.

CARACTERÍSTICAS:
✅ Modo de razonamiento (thinking mode) habilitado
✅ Soporte completo para tool calls
✅ Preservación automática de reasoning_content
✅ Compatible con todas las funciones de AutoGen

MODELOS SOPORTADOS:
- deepseek-reasoner (R1) - Recomendado
- deepseek-chat + thinking mode
- deepseek-r1
═══════════════════════════════════════════════════════════════
```

---

## 📋 ¿Qué es el Modo de Razonamiento?

El modo de razonamiento (thinking mode) de DeepSeek R1:

1. **Genera razonamiento interno** antes de responder
2. **Mejora la precisión** en tareas complejas
3. **Muestra el proceso** de pensamiento del modelo
4. **Optimiza tool calls** mediante razonamiento previo

### Ejemplo de Flujo

```
Usuario: "¿Cuántas Rs hay en 'strawberry'?"

Modelo (reasoning_content - interno):
"Necesito contar las Rs en la palabra 'strawberry'.
Voy a revisar letra por letra: s-t-r-a-w-b-e-r-r-y.
Encuentro R en posiciones: 3, 8, 9.
Total: 3 Rs."

Modelo (content - respuesta):
"La palabra 'strawberry' contiene 3 letras 'R'."
```

---

## 🏗️ Arquitectura de la Solución

### Componentes Implementados

#### 1. `DeepSeekReasoningClient`
**Ubicación:** [src/utils/deepseek_reasoning_client.py](../src/utils/deepseek_reasoning_client.py)

Cliente que extiende `OpenAIChatCompletionClient` para:
- ✅ Inyectar `extra_body={"thinking": {"type": "enabled"}}`
- ✅ Cachear `reasoning_content` de respuestas
- ✅ Preservar `reasoning_content` en tool calls múltiples
- ✅ Soportar streaming con thinking mode

#### 2. Funciones de Configuración
**Ubicación:** [src/utils/deepseek_fix.py](../src/utils/deepseek_fix.py)

- `should_use_reasoning_client()` - Detecta si usar el cliente especial
- `get_thinking_mode_enabled()` - Determina si habilitar thinking mode
- `DEEPSEEK_REASONER_INFO` - Mensaje informativo

#### 3. Integración en Main
**Ubicación:** [main.py:75-126](../main.py#L75-L126)

Detección automática y selección del cliente apropiado.

---

## 🔧 Implementación Técnica

### Problema Resuelto

**Error Original:**
```
Error code: 400 - {'error': {'message': 'Missing `reasoning_content` field
in the assistant message at message index X'}}
```

**Causa:**
AutoGen convierte mensajes a `LLMMessage` y no preserva campos custom como `reasoning_content`.

**Solución:**
`DeepSeekReasoningClient` intercepta las llamadas y:

```python
# 1. Inyecta thinking mode
extra_args["thinking"] = {"type": "enabled"}

# 2. Extrae reasoning_content de respuestas
reasoning_content = response.choices[0].message.reasoning_content

# 3. Cachea para uso futuro
self._reasoning_cache[content_key] = reasoning_content

# 4. Lo preserva en siguientes tool calls
```

### Según Documentación DeepSeek

**Requerimientos de la API:**

1. Habilitar thinking mode:
   ```python
   extra_body={"thinking": {"type": "enabled"}}
   ```

2. Preservar reasoning_content en tool calls:
   ```python
   messages.append(response.choices[0].message)  # Incluye reasoning_content
   ```

3. No enviar reasoning_content en nuevos turns:
   ```python
   clear_reasoning_content(messages)  # Antes de nuevo turn
   ```

**Nuestra implementación sigue exactamente estas reglas.**

---

## 💻 Uso Programático

### Opción 1: Usar DaveAgent CLI (Recomendado)

```bash
# Configurar modelo en .env
echo "DAVEAGENT_MODEL=deepseek-reasoner" >> .daveagent/.env

# Ejecutar
daveagent
```

### Opción 2: Usar el Cliente Directamente

```python
from src.utils.deepseek_reasoning_client import DeepSeekReasoningClient
from autogen_core.models import UserMessage

# Crear cliente
client = DeepSeekReasoningClient(
    model="deepseek-reasoner",
    api_key="your-api-key",
    base_url="https://api.deepseek.com"
)

# Usar
result = await client.create([
    UserMessage(content="Tu pregunta", source="user")
])

print(f"Respuesta: {result.content}")

# Acceder al razonamiento (si disponible)
reasoning = getattr(result, 'reasoning_content', None)
if reasoning:
    print(f"Razonamiento: {reasoning}")

# Cerrar
await client.close()
```

### Opción 3: Con Agentes de AutoGen

```python
from autogen_agentchat.agents import AssistantAgent
from src.utils.deepseek_reasoning_client import DeepSeekReasoningClient

# Crear model client
model_client = DeepSeekReasoningClient(
    model="deepseek-reasoner",
    api_key="your-api-key",
    base_url="https://api.deepseek.com"
)

# Crear agente
agent = AssistantAgent(
    name="ReasoningAgent",
    model_client=model_client,
    tools=[...]  # Tool calls funcionan perfectamente
)

# Usar
result = await agent.run(task="Tu tarea compleja")
```

---

## 🧪 Testing con Tool Calls

### Test 1: Tool Calls Simples

```python
# Pregunta que requiere tool calls
"Lista los archivos en el directorio src y cuéntame cuántos son Python"
```

**Resultado Esperado:**
```
💭 Reasoning: "Necesito primero listar archivos con list_dir,
               luego filtrar los .py y contarlos"
✅ Tool: list_dir(src/)
💭 Reasoning: "Veo 45 archivos, debo contar solo .py"
📝 Respuesta: "Hay 23 archivos Python en src/"
```

### Test 2: Tool Calls Múltiples

```python
# Pregunta compleja con múltiples pasos
"Busca la función main en el código, lee su contenido y explica qué hace"
```

**Resultado Esperado:**
```
💭 Reasoning: "Buscaré con search_code, luego read_file"
✅ Tool 1: search_code("main")
✅ Tool 2: read_file("main.py")
💭 Reasoning: "Analizando el código..."
📝 Respuesta: "La función main inicializa..."
```

### Test 3: Razonamiento Complejo

```python
# Pregunta que requiere razonamiento matemático
"Si tengo 9.11 y 9.8, ¿cuál es mayor?"
```

**Resultado Esperado:**
```
💭 Reasoning: "Comparando 9.11 vs 9.8 como decimales:
               9.11 = 9 + 0.11
               9.8 = 9 + 0.80
               0.80 > 0.11
               Por tanto 9.8 > 9.11"
📝 Respuesta: "9.8 es mayor que 9.11"
```

---

## 📊 Comparación: Con vs Sin Thinking Mode

| Característica | Sin Thinking | Con Thinking (R1) |
|----------------|--------------|-------------------|
| **Velocidad** | Más rápido | Ligeramente más lento |
| **Precisión** | Buena | Excelente |
| **Razonamiento visible** | ❌ No | ✅ Sí |
| **Tareas complejas** | Puede fallar | Mejor rendimiento |
| **Tool calls** | ✅ Funciona | ✅ Funciona mejor |
| **Costo (tokens)** | Menor | Mayor (incluye reasoning) |

---

## 🎯 Casos de Uso Recomendados

### Ideal para Thinking Mode:

✅ Análisis de código complejo
✅ Debugging con múltiples pasos
✅ Planificación de tareas
✅ Razonamiento matemático/lógico
✅ Tareas que requieren múltiples tool calls
✅ Problemas que necesitan "pensar en voz alta"

### No necesario para:

❌ Respuestas simples y directas
❌ Traducciones
❌ Formateo de texto
❌ Operaciones CRUD básicas

---

## 🔍 Debugging y Logs

### Ver Reasoning Content

El `reasoning_content` se captura en:

1. **Logs de la aplicación** (`.daveagent/logs/`)
   ```
   💭 Reasoning content received: 1234 chars
   💾 Cached reasoning_content with key: ...
   ```

2. **JSON Logger** (`.daveagent/llm_interactions.json`)
   ```json
   {
     "event_type": "llm_call",
     "model": "deepseek-reasoner",
     "reasoning_content": "El proceso de razonamiento...",
     "response": "La respuesta final"
   }
   ```

3. **Langfuse** (si está habilitado)
   Traza completa con reasoning visible

### Cache Stats

```python
# Ver estadísticas del cache
stats = client.get_cache_stats()
print(stats)
# {
#   "cached_entries": 5,
#   "total_reasoning_chars": 12345,
#   "cache_keys": [...]
# }

# Limpiar cache (nueva conversación)
client.clear_reasoning_cache()
```

---

## ⚙️ Configuración Avanzada

### Habilitar Thinking Explícitamente

```python
client = DeepSeekReasoningClient(
    model="deepseek-chat",  # No es deepseek-reasoner
    enable_thinking=True,    # Forzar thinking mode
    # ... otros parámetros
)
```

### Desactivar Thinking

```python
client = DeepSeekReasoningClient(
    model="deepseek-reasoner",
    enable_thinking=False,   # Desactivar thinking
    # ... otros parámetros
)
```

### Configurar Max Tokens

```python
# Thinking mode puede usar más tokens
client = DeepSeekReasoningClient(
    model="deepseek-reasoner",
    max_tokens=64000,  # Máximo para reasoning
    # ... otros parámetros
)
```

---

## 📚 Referencias

### Documentación Oficial

- [DeepSeek Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode)
- [Tool Calls con Thinking](https://api-docs.deepseek.com/guides/thinking_mode#tool-calls)
- [AutoGen OpenAI Client](https://docs.ag2.ai/docs/api/autogen_ext.models.openai)

### Código Fuente

- [DeepSeekReasoningClient](../src/utils/deepseek_reasoning_client.py)
- [Configuración](../src/utils/deepseek_fix.py)
- [Integración en Main](../main.py)

---

## 🎉 Resumen

### Lo Que Funciona

✅ **DeepSeek R1 con thinking mode**
✅ **Tool calls múltiples**
✅ **Preservación de reasoning_content**
✅ **Streaming con razonamiento**
✅ **Cache automático**
✅ **Compatible con todos los agentes**

### Beneficios

🚀 **Mayor precisión** en tareas complejas
🧠 **Razonamiento visible** para debugging
🔧 **Mejor tool calls** mediante planificación
📊 **Trazabilidad completa** en logs

### Próximos Pasos

1. **Probar con tu configuración**
2. **Ver reasoning en los logs**
3. **Experimentar con tareas complejas**
4. **Reportar feedback** si encuentras issues

---

**¡Disfruta del poder del razonamiento extendido de DeepSeek R1!** 🧠✨

_Última actualización: 2025-12-04_
_Implementado por: DaveAgent Team_
