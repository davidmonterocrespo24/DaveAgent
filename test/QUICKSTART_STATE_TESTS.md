# 🎯 Guía Rápida: Tests de AutoGen State Management

## ¿Qué son estos tests?

Pruebas exhaustivas para entender cómo funciona el sistema de estados de AutoGen (`save_state()` y `load_state()`), especialmente enfocado en:

✅ **Cómo guardar sesiones de conversación completas**
✅ **Cómo cargar y continuar conversaciones**
✅ **Cómo visualizar el historial en consola**
✅ **Cómo gestionar múltiples sesiones**

## 🚀 Inicio Rápido

### 1. Preparar Entorno

```bash
# Instalar dependencias
pip install -r requirements.txt
pip install rich  # Para visualización mejorada

# Configurar API key en .env
echo "DEEPSEEK_API_KEY=tu_api_key_aqui" > .env
```

### 2. Ejecutar Todos los Tests

```bash
# Opción 1: Script todo-en-uno
python test/run_all_state_tests.py

# Opción 2: Individual (recomendado para aprender)
python test/test_autogen_state_basics.py
python test/test_autogen_state_sessions.py
python test/test_autogen_state_history_viewer.py
python test/test_autogen_state_resume.py
```

## 📋 Tests Incluidos

| Test | Descripción | Qué Aprenderás |
|------|-------------|----------------|
| **test_autogen_state_basics.py** | Conceptos básicos | Estructura del estado, save/load |
| **test_autogen_state_sessions.py** | Sesiones múltiples | Crear, listar, cargar sesiones |
| **test_autogen_state_history_viewer.py** | Visualización | Mostrar historial en consola |
| **test_autogen_state_resume.py** ⭐ | Continuación | Flujo completo de resume de sesión |

## 🎓 Conceptos Clave

### 1. El Estado es un Diccionario Simple

```python
agent_state = await agent.save_state()

# Estructura:
{
    "type": "AssistantAgentState",
    "version": "1.0.0",
    "llm_messages": [...]  # ← Todo el historial aquí
}
```

### 2. Acceder a los Mensajes

```python
messages = agent_state["llm_messages"]

for msg in messages:
    if msg["type"] == "UserMessage":
        print(f"👤 {msg['content']}")
    elif msg["type"] == "AssistantMessage":
        print(f"🤖 {msg['content']}")
```

### 3. Guardar y Cargar

```python
import json

# Guardar
agent_state = await agent.save_state()
with open("session.json", "w") as f:
    json.dump(agent_state, f, indent=2, default=str)

# Cargar (en nueva sesión)
with open("session.json", "r") as f:
    agent_state = json.load(f)

new_agent = AssistantAgent(...)
await new_agent.load_state(agent_state)
# ✅ new_agent recuerda toda la conversación
```

## 💡 Caso de Uso Real

### Flujo de Trabajo con Sesiones

```python
# SESIÓN 1: Usuario trabaja y guarda
async def session_1():
    agent = AssistantAgent(...)
    
    # Conversación
    await agent.on_messages([msg1], token)
    await agent.on_messages([msg2], token)
    
    # Guardar al finalizar
    state = await agent.save_state()
    save_to_file("my_work.json", state)

# SESIÓN 2: Usuario retoma trabajo (días después)
async def session_2():
    # Cargar sesión
    state = load_from_file("my_work.json")
    
    # Nuevo agente con estado cargado
    agent = AssistantAgent(...)
    await agent.load_state(state)
    
    # Continuar donde se dejó
    await agent.on_messages([msg3], token)
    # ✅ Agente recuerda msg1 y msg2
```

## 📊 Estructura del Estado

```
agent_state
├── type: "AssistantAgentState"
├── version: "1.0.0"
└── llm_messages: [
    ├── {type: "UserMessage", content: "...", source: "user"}
    ├── {type: "AssistantMessage", content: "...", source: "agent"}
    ├── {type: "UserMessage", content: "...", source: "user"}
    └── {type: "AssistantMessage", content: "...", source: "agent"}
]
```

## 🔍 ¿Qué Guardar?

AutoGen guarda **AUTOMÁTICAMENTE**:
- ✅ Todos los mensajes del usuario
- ✅ Todas las respuestas del agente
- ✅ Orden cronológico exacto
- ✅ Contexto completo de la conversación

**NO necesitas:**
- ❌ Comprimir historial manualmente
- ❌ Gestionar límites de tokens
- ❌ Crear resúmenes

AutoGen lo maneja todo por ti! 🎉

## 📁 Archivos Generados por los Tests

Después de ejecutar los tests, encontrarás:

```
test/
├── .temp_test_state.json              # Estado básico de ejemplo
├── .temp_state_analysis.json          # Análisis de estructura
├── .temp_history_example.json         # Ejemplo de historial
├── .temp_resume_session.json          # Sesión de continuación
└── .temp_sessions/                    # Sesiones múltiples
    ├── session_python_work.json
    ├── session_javascript_work.json
    └── session_personal_chat.json
```

**💡 Tip:** Abre estos archivos JSON para ver la estructura real del estado.

## 📚 Documentación Completa

- **[README_STATE_TESTS.md](./README_STATE_TESTS.md)** - Guía completa de tests
- **[../docs/AUTOGEN_STATE_STRUCTURE.md](../docs/AUTOGEN_STATE_STRUCTURE.md)** - Estructura del estado en detalle
- **[../docs/MIGRATION_TO_AUTOGEN_STATE.md](../docs/MIGRATION_TO_AUTOGEN_STATE.md)** - Migración desde sistema legacy

## 🎯 Test Recomendado para Empezar

Si solo vas a ejecutar UN test, ejecuta:

```bash
python test/test_autogen_state_resume.py
```

Este test te muestra el flujo completo:
1. 🎬 Conversación inicial
2. 💾 Guardado de estado
3. 🔌 Simulación de cierre de app
4. 📂 Carga de estado
5. 💬 Continuación de conversación
6. ✅ Verificación de memoria completa

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| "DEEPSEEK_API_KEY no encontrada" | Crea archivo `.env` con tu API key |
| "Import autogen_agentchat could not be resolved" | Ejecuta `pip install -r requirements.txt` |
| "Import rich could not be resolved" | Ejecuta `pip install rich` |
| Los tests no muestran conversación | Verifica que tu API key de DeepSeek sea válida |

## 🎓 Lo Que Aprenderás

Después de ejecutar estos tests, entenderás:

1. ✅ Cómo AutoGen guarda TODO el contexto de conversación
2. ✅ Cómo restaurar conversaciones entre reinicios
3. ✅ Cómo acceder y manipular el historial
4. ✅ Cómo implementar un sistema de sesiones
5. ✅ Por qué NO necesitas gestión manual de contexto

## 🚀 Próximos Pasos

1. **Ejecuta los tests** - Especialmente `test_autogen_state_resume.py`
2. **Inspecciona los archivos JSON** generados
3. **Lee la documentación** en `docs/AUTOGEN_STATE_STRUCTURE.md`
4. **Implementa tu sistema** basado en los ejemplos

## 📞 Preguntas Frecuentes

**P: ¿Cuánto historial se guarda?**
R: TODO el historial de la conversación. AutoGen no tiene límites arbitrarios.

**P: ¿Necesito comprimir el historial manualmente?**
R: NO. AutoGen gestiona el contexto automáticamente.

**P: ¿Puedo editar el estado manualmente?**
R: Técnicamente sí (es un dict), pero NO es recomendado. Usa `save_state()` y `load_state()`.

**P: ¿El estado es compatible entre versiones?**
R: Sí, el campo `version` asegura compatibilidad.

**P: ¿Puedo guardar el estado en una base de datos?**
R: Sí! Es un dict serializable. Puedes guardarlo en JSON, SQLite, MongoDB, etc.

---

**Última actualización:** 2025-11-05  
**Versión:** 1.0  
**Autor:** DaveAgent Team

