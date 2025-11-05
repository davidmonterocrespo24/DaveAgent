## 🔍 Estructura del Estado de AutoGen

Este documento explica en detalle la estructura interna del objeto de estado que devuelve `save_state()` en AutoGen.

## 📊 Estructura General

Cuando llamas a `agent.save_state()`, obtienes un **diccionario** con esta estructura:

```python
{
    "type": "AssistantAgentState",
    "version": "1.0.0",
    "llm_messages": [
        # Lista de todos los mensajes de la conversación
    ]
}
```

## 🔑 Campos Principales

### 1. `type` (string)
- **Descripción**: Tipo de estado guardado
- **Valores comunes**: `"AssistantAgentState"`, `"TeamState"`, etc.
- **Uso**: Identificar qué tipo de agente/equipo creó el estado

```python
agent_state["type"]  # → "AssistantAgentState"
```

### 2. `version` (string)
- **Descripción**: Versión del formato de estado
- **Valor típico**: `"1.0.0"`
- **Uso**: Compatibilidad entre versiones de AutoGen

```python
agent_state["version"]  # → "1.0.0"
```

### 3. `llm_messages` (list)
- **Descripción**: **CAMPO MÁS IMPORTANTE** - Lista de todos los mensajes de la conversación
- **Tipo**: Lista de diccionarios
- **Contenido**: Cada mensaje es un dict con información completa del mensaje

```python
messages = agent_state["llm_messages"]
print(f"Total de mensajes: {len(messages)}")
```

## 📝 Estructura de un Mensaje

Cada elemento en `llm_messages` es un diccionario con esta estructura:

### Mensaje del Usuario (UserMessage)

```python
{
    "type": "UserMessage",
    "content": "What is the capital of France?",
    "source": "user"
}
```

**Campos:**
- `type`: `"UserMessage"` - Indica que es un mensaje del usuario
- `content`: El texto del mensaje
- `source`: `"user"` - Quién envió el mensaje

### Mensaje del Asistente (AssistantMessage)

```python
{
    "type": "AssistantMessage",
    "content": "The capital of France is Paris.",
    "source": "agent_name"
}
```

**Campos:**
- `type`: `"AssistantMessage"` - Respuesta del agente
- `content`: La respuesta generada
- `source`: Nombre del agente que respondió

### Ejemplo Completo de Historial

```python
{
    "type": "AssistantAgentState",
    "version": "1.0.0",
    "llm_messages": [
        {
            "type": "UserMessage",
            "content": "Hello! My name is John.",
            "source": "user"
        },
        {
            "type": "AssistantMessage",
            "content": "Hello John! How can I help you today?",
            "source": "assistant"
        },
        {
            "type": "UserMessage",
            "content": "What's my name?",
            "source": "user"
        },
        {
            "type": "AssistantMessage",
            "content": "Your name is John.",
            "source": "assistant"
        }
    ]
}
```

## 🛠️ Cómo Acceder a los Mensajes

### Obtener todos los mensajes

```python
# Después de load_state()
agent_state = await agent.save_state()

# Acceder a los mensajes
messages = agent_state["llm_messages"]

print(f"Total de mensajes: {len(messages)}")
```

### Iterar sobre mensajes

```python
for i, msg in enumerate(messages, 1):
    msg_type = msg["type"]
    content = msg["content"]
    source = msg["source"]
    
    if msg_type == "UserMessage":
        print(f"[{i}] 👤 Usuario: {content}")
    elif msg_type == "AssistantMessage":
        print(f"[{i}] 🤖 {source}: {content}")
```

### Filtrar mensajes por tipo

```python
# Solo mensajes del usuario
user_messages = [
    msg for msg in messages 
    if msg["type"] == "UserMessage"
]

# Solo mensajes del asistente
assistant_messages = [
    msg for msg in messages 
    if msg["type"] == "AssistantMessage"
]

print(f"Mensajes del usuario: {len(user_messages)}")
print(f"Respuestas del asistente: {len(assistant_messages)}")
```

### Obtener último mensaje

```python
if messages:
    last_message = messages[-1]
    print(f"Último mensaje: {last_message['content']}")
```

### Obtener conversación reciente

```python
# Últimos 10 mensajes
recent_messages = messages[-10:]

for msg in recent_messages:
    print(f"{msg['source']}: {msg['content']}")
```

## 🎯 Casos de Uso Prácticos

### 1. Mostrar Historial en Consola

```python
def display_conversation_history(agent_state: dict):
    """Muestra todo el historial de conversación"""
    
    messages = agent_state.get("llm_messages", [])
    
    print(f"\n📜 HISTORIAL ({len(messages)} mensajes)\n")
    print("=" * 80)
    
    for i, msg in enumerate(messages, 1):
        msg_type = msg["type"]
        content = msg["content"]
        
        if msg_type == "UserMessage":
            print(f"\n👤 Usuario:")
            print(f"   {content}")
        elif msg_type == "AssistantMessage":
            print(f"\n🤖 Asistente:")
            print(f"   {content}")
    
    print("\n" + "=" * 80)
```

### 2. Exportar Historial a Texto

```python
def export_conversation_to_text(agent_state: dict, output_file: str):
    """Exporta conversación a archivo de texto"""
    
    messages = agent_state.get("llm_messages", [])
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("HISTORIAL DE CONVERSACIÓN\n")
        f.write("=" * 80 + "\n\n")
        
        for msg in messages:
            if msg["type"] == "UserMessage":
                f.write(f"USUARIO:\n{msg['content']}\n\n")
            elif msg["type"] == "AssistantMessage":
                f.write(f"ASISTENTE:\n{msg['content']}\n\n")
```

### 3. Buscar en el Historial

```python
def search_in_history(agent_state: dict, search_term: str):
    """Busca un término en el historial"""
    
    messages = agent_state.get("llm_messages", [])
    results = []
    
    for i, msg in enumerate(messages, 1):
        content = msg["content"].lower()
        if search_term.lower() in content:
            results.append({
                "index": i,
                "type": msg["type"],
                "content": msg["content"]
            })
    
    return results

# Uso
results = search_in_history(agent_state, "python")
print(f"Encontrados {len(results)} mensajes con 'python'")
```

### 4. Estadísticas del Historial

```python
def get_conversation_stats(agent_state: dict):
    """Obtiene estadísticas de la conversación"""
    
    messages = agent_state.get("llm_messages", [])
    
    user_count = sum(1 for msg in messages if msg["type"] == "UserMessage")
    assistant_count = sum(1 for msg in messages if msg["type"] == "AssistantMessage")
    
    total_user_chars = sum(
        len(msg["content"]) 
        for msg in messages 
        if msg["type"] == "UserMessage"
    )
    
    total_assistant_chars = sum(
        len(msg["content"]) 
        for msg in messages 
        if msg["type"] == "AssistantMessage"
    )
    
    return {
        "total_messages": len(messages),
        "user_messages": user_count,
        "assistant_messages": assistant_count,
        "total_user_chars": total_user_chars,
        "total_assistant_chars": total_assistant_chars,
        "avg_user_message_length": total_user_chars / user_count if user_count > 0 else 0,
        "avg_assistant_message_length": total_assistant_chars / assistant_count if assistant_count > 0 else 0
    }

# Uso
stats = get_conversation_stats(agent_state)
print(f"Total: {stats['total_messages']} mensajes")
print(f"Usuario: {stats['user_messages']} mensajes")
print(f"Asistente: {stats['assistant_messages']} mensajes")
```

## 🔄 Estado de Teams

Cuando guardas el estado de un **Team** (no un agente individual), la estructura es diferente:

```python
{
    "type": "TeamState",
    "version": "1.0.0",
    "agent_states": {
        "agent_1_id": {
            "type": "ChatAgentContainerState",
            "agent_state": {
                "type": "AssistantAgentState",
                "llm_messages": [...]
            }
        },
        "agent_2_id": { ... }
    },
    "team_id": "unique_team_id"
}
```

### Acceder a mensajes de un agente específico en un team:

```python
team_state = await team.save_state()

# Obtener estados de todos los agentes
agent_states = team_state["agent_states"]

# Acceder a un agente específico
for agent_id, agent_container in agent_states.items():
    if "agent_state" in agent_container:
        agent_state = agent_container["agent_state"]
        
        if "llm_messages" in agent_state:
            messages = agent_state["llm_messages"]
            print(f"Agent {agent_id}: {len(messages)} mensajes")
```

## 💾 Persistencia

### Guardar a JSON

```python
import json

# Guardar
agent_state = await agent.save_state()

with open("conversation_state.json", "w") as f:
    json.dump(agent_state, f, indent=2, default=str)
```

### Cargar desde JSON

```python
import json

# Cargar
with open("conversation_state.json", "r") as f:
    agent_state = json.load(f)

# Restaurar en agente
await agent.load_state(agent_state)
```

## ⚠️ Notas Importantes

1. **El estado es un dict simple** - Puedes manipularlo como cualquier diccionario de Python
2. **Los mensajes están ordenados cronológicamente** - El primer mensaje es el más antiguo
3. **No modifiques el estado manualmente** - Usa `save_state()` y `load_state()`
4. **El estado es serializable** - Puedes guardarlo en JSON, bases de datos, etc.
5. **Versionado** - El campo `version` asegura compatibilidad futura

## 🎓 Ejemplos de Uso Real

### UI de Chat

```python
def render_chat_ui(agent_state: dict):
    """Renderiza UI de chat con el historial"""
    
    messages = agent_state.get("llm_messages", [])
    
    for msg in messages:
        if msg["type"] == "UserMessage":
            render_user_bubble(msg["content"])
        elif msg["type"] == "AssistantMessage":
            render_assistant_bubble(msg["content"])
```

### Sistema de Búsqueda

```python
def create_searchable_index(agent_state: dict):
    """Crea índice de búsqueda del historial"""
    
    messages = agent_state.get("llm_messages", [])
    index = {}
    
    for i, msg in enumerate(messages):
        words = msg["content"].lower().split()
        for word in words:
            if word not in index:
                index[word] = []
            index[word].append(i)
    
    return index
```

### Análisis de Conversación

```python
def analyze_conversation_topics(agent_state: dict):
    """Analiza temas de la conversación"""
    
    messages = agent_state.get("llm_messages", [])
    
    # Concatenar todo el contenido
    all_text = " ".join(msg["content"] for msg in messages)
    
    # Análisis simple de palabras frecuentes
    from collections import Counter
    words = all_text.lower().split()
    common_words = Counter(words).most_common(10)
    
    return common_words
```

## 📚 Referencias

- [AutoGen State Management Docs](https://microsoft.github.io/autogen/docs/tutorial/state-management)
- Tests de ejemplo: `test/test_autogen_state_*.py`
- StateManager implementation: `src/managers/state_manager.py`

---

**Última actualización:** 2025-11-05
**Versión:** 1.0
