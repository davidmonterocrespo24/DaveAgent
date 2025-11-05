# 🧪 Tests de AutoGen State Management

Esta carpeta contiene tests exhaustivos para entender y demostrar cómo funciona el sistema de estados de AutoGen (`save_state()` y `load_state()`).

## 📋 Tests Disponibles

### 1. `test_autogen_state_basics.py` 
**Test básico de save_state/load_state**

Demuestra:
- ✅ Cómo funciona `save_state()` en un agente
- ✅ La estructura del objeto de estado
- ✅ Cómo funciona `load_state()` para restaurar
- ✅ Qué información se persiste exactamente
- ✅ Exploración profunda de la estructura del estado

**Ejecutar:**
```bash
python test/test_autogen_state_basics.py
```

**Archivos generados:**
- `test/.temp_test_state.json` - Estado guardado de ejemplo
- `test/.temp_state_analysis.json` - Análisis completo de estructura

---

### 2. `test_autogen_state_sessions.py`
**Test de sesiones múltiples**

Demuestra:
- ✅ Crear múltiples sesiones de conversación
- ✅ Guardar cada sesión con un ID único
- ✅ Listar todas las sesiones guardadas
- ✅ Cargar una sesión específica
- ✅ Continuar conversación desde sesión cargada

**Ejecutar:**
```bash
python test/test_autogen_state_sessions.py
```

**Archivos generados:**
- `test/.temp_sessions/session_python_work.json`
- `test/.temp_sessions/session_javascript_work.json`
- `test/.temp_sessions/session_personal_chat.json`

**Salida esperada:**
```
📝 CREANDO SESIÓN: python_work
[1/3] 👤 Usuario: I'm learning Python. Can you help me?
[1/3] 🤖 Agente: Of course! I'd be happy to help you learn Python...

📋 LISTANDO TODAS LAS SESIONES
✅ Total de sesiones: 3

1. personal_chat
   Guardada: 2025-11-05T14:30:22
   Mensajes: 3
```

---

### 3. `test_autogen_state_history_viewer.py`
**Test de visualización de historial**

Demuestra:
- ✅ Extraer mensajes históricos de un estado
- ✅ Mostrar historial en consola con formato
- ✅ Visualización tipo chat con Rich
- ✅ Diferentes formatos de presentación

**Ejecutar:**
```bash
python test/test_autogen_state_history_viewer.py
```

**Requiere:**
- `pip install rich` (para visualización mejorada)

**Salida esperada:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 👤 Usuario (#1)                                         ┃
┠──────────────────────────────────────────────────────────┨
┃ Hi! I need help with Python decorators.                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🤖 Asistente (#2)                                       ┃
┠──────────────────────────────────────────────────────────┨
┃ Decorators in Python are...                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

### 4. `test_autogen_state_resume.py` ⭐
**Test de continuación de conversación (MÁS IMPORTANTE)**

Demuestra el flujo completo:
- ✅ Sesión 1: Conversación inicial → Guarda estado → Cierra app
- ✅ Sesión 2: Abre app → Carga estado → Continúa conversación
- ✅ Sesión 3: Verificación de que el agente recuerda TODO

**Ejecutar:**
```bash
python test/test_autogen_state_resume.py
```

**Archivos generados:**
- `test/.temp_resume_session.json` - Sesión de prueba

**Flujo del test:**
```
🎬 SESIÓN 1: CONVERSACIÓN INICIAL
💬 Usuario: "Hi! I'm working on a Python project."
🤖 Agente: "Great! I'd be happy to help..."
💾 Guardando estado...
⏸️ Simulando cierre de aplicación...

🔄 SESIÓN 2: CARGANDO ESTADO Y CONTINUANDO
📂 Cargando estado guardado...
📜 HISTORIAL PREVIO (mostrando conversación anterior)
💬 Usuario: "Can you remember what framework we were discussing?"
🤖 Agente: "Yes, we were discussing FastAPI..."

🔍 SESIÓN 3: VERIFICACIÓN FINAL
❓ Usuario: "Can you summarize our entire conversation?"
🤖 Agente: "We started by discussing Python projects..."
```

---

## 🚀 Cómo Ejecutar Todos los Tests

### Opción 1: Individual
```bash
# Test básico
python test/test_autogen_state_basics.py

# Test de sesiones
python test/test_autogen_state_sessions.py

# Test de visualización
python test/test_autogen_state_history_viewer.py

# Test de continuación (RECOMENDADO)
python test/test_autogen_state_resume.py
```

### Opción 2: Script de ejecución
```bash
# Crear script run_state_tests.py
cat > run_state_tests.py << 'EOF'
import asyncio
import subprocess

tests = [
    "test/test_autogen_state_basics.py",
    "test/test_autogen_state_sessions.py",
    "test/test_autogen_state_history_viewer.py",
    "test/test_autogen_state_resume.py",
]

for test in tests:
    print(f"\n{'='*80}")
    print(f"Ejecutando: {test}")
    print('='*80)
    subprocess.run(["python", test])
EOF

python run_state_tests.py
```

## 📚 Documentación Relacionada

- **[AUTOGEN_STATE_STRUCTURE.md](../docs/AUTOGEN_STATE_STRUCTURE.md)** - Estructura detallada del objeto de estado
- **[MIGRATION_TO_AUTOGEN_STATE.md](../docs/MIGRATION_TO_AUTOGEN_STATE.md)** - Guía de migración
- **[STATE_MANAGEMENT.md](../docs/STATE_MANAGEMENT.md)** - Documentación del StateManager

## 🔧 Requisitos

### Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto:

```bash
DEEPSEEK_API_KEY=your_api_key_here
```

### Dependencias
```bash
pip install -r requirements.txt

# Para visualización mejorada:
pip install rich
```

## 📁 Archivos Generados

Los tests generan archivos temporales en `test/.temp_*`:

```
test/
├── .temp_test_state.json          # Estado de test básico
├── .temp_state_analysis.json      # Análisis de estructura
├── .temp_history_example.json     # Ejemplo de historial
├── .temp_resume_session.json      # Sesión de prueba de continuación
└── .temp_sessions/                # Sesiones múltiples
    ├── session_python_work.json
    ├── session_javascript_work.json
    └── session_personal_chat.json
```

**Nota:** Estos archivos son temporales y puedes eliminarlos sin problema.

## 🎯 Objetivos de los Tests

1. **Entender save_state/load_state**
   - Qué información se guarda
   - Cómo se estructura
   - Cómo se restaura

2. **Gestión de Sesiones**
   - Crear múltiples sesiones
   - Listar sesiones disponibles
   - Cargar sesión específica

3. **Visualización de Historial**
   - Extraer mensajes del estado
   - Formatear para UI
   - Diferentes presentaciones

4. **Continuidad de Conversación**
   - Guardar estado entre sesiones
   - Recuperar contexto completo
   - Continuar sin pérdida de información

## 💡 Conceptos Clave Demostrados

### 1. Estado es un Dict Simple
```python
agent_state = await agent.save_state()
print(type(agent_state))  # <class 'dict'>
```

### 2. Mensajes en `llm_messages`
```python
messages = agent_state["llm_messages"]
for msg in messages:
    print(f"{msg['type']}: {msg['content']}")
```

### 3. Persistencia con JSON
```python
import json

# Guardar
with open("session.json", "w") as f:
    json.dump(agent_state, f, indent=2, default=str)

# Cargar
with open("session.json", "r") as f:
    agent_state = json.load(f)

await agent.load_state(agent_state)
```

### 4. Continuidad Total
```python
# Sesión 1
response1 = await agent.on_messages([msg1], token)
state = await agent.save_state()

# Sesión 2 (después de reiniciar)
new_agent = AssistantAgent(...)
await new_agent.load_state(state)
response2 = await new_agent.on_messages([msg2], token)
# ✅ new_agent recuerda msg1
```

## 🐛 Troubleshooting

### Error: "DEEPSEEK_API_KEY no encontrada"
**Solución:** Crea archivo `.env` con tu API key

### Error: "Import autogen_agentchat could not be resolved"
**Solución:** Instala dependencias
```bash
pip install -r requirements.txt
```

### Error: "Import rich could not be resolved"
**Solución:** Instala rich
```bash
pip install rich
```

### Los tests no muestran conversación
**Solución:** Verifica que tu API key de DeepSeek sea válida

## 📊 Estructura del Estado (Resumen)

```python
{
    "type": "AssistantAgentState",
    "version": "1.0.0",
    "llm_messages": [
        {
            "type": "UserMessage",
            "content": "mensaje del usuario",
            "source": "user"
        },
        {
            "type": "AssistantMessage", 
            "content": "respuesta del agente",
            "source": "agent_name"
        }
    ]
}
```

## 🎓 Aprendizaje

Después de ejecutar estos tests, entenderás:

✅ Cómo AutoGen guarda TODO el contexto de conversación
✅ Cómo restaurar conversaciones entre reinicios de aplicación
✅ Cómo acceder y manipular el historial de mensajes
✅ Cómo implementar un sistema de sesiones completo
✅ Por qué NO necesitas comprimir historial manualmente

## 🚀 Próximos Pasos

Después de ejecutar los tests:

1. Revisa los archivos `.json` generados
2. Lee `docs/AUTOGEN_STATE_STRUCTURE.md` para detalles
3. Implementa tu propio sistema de sesiones basado en los ejemplos
4. Integra visualización de historial en tu UI

---

**Última actualización:** 2025-11-05
**Autor:** CodeAgent Team
