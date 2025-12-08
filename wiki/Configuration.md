# ⚙️ Configuración - CodeAgent

Esta guía documenta todas las opciones de configuración disponibles para personalizar CodeAgent.

## 📁 Archivos de Configuración

### 1. `.env` - Variables de Entorno

Crea un archivo `.env` en el directorio raíz del proyecto:

```env
# ==================== API Configuration ====================
DAVEAGENT_API_KEY=your-api-key-here
DAVEAGENT_MODEL=deepseek-chat
DAVEAGENT_BASE_URL=https://api.deepseek.com/v1

# ==================== SSL Configuration ====================
DAVEAGENT_SSL_VERIFY=true

# ==================== Memory Configuration ====================
DAVEAGENT_MEMORY_PATH=.daveagent/memory
DAVEAGENT_AUTO_INDEX=false

# ==================== Logging Configuration ====================
DAVEAGENT_LOG_LEVEL=INFO
DAVEAGENT_LOG_PATH=logs/

# ==================== Agent Configuration ====================
DAVEAGENT_MAX_TOKENS=8000
DAVEAGENT_SUMMARY_THRESHOLD=6000
DAVEAGENT_TEMPERATURE=0.7
```

---

## 🔑 Configuración de API

### Proveedores Soportados

CodeAgent soporta cualquier proveedor compatible con la API de OpenAI.

#### DeepSeek (Por Defecto)

```env
DAVEAGENT_API_KEY=sk-your-deepseek-key
DAVEAGENT_MODEL=deepseek-chat
DAVEAGENT_BASE_URL=https://api.deepseek.com/v1
```

#### OpenAI

```env
DAVEAGENT_API_KEY=sk-your-openai-key
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_BASE_URL=https://api.openai.com/v1
```

#### Azure OpenAI

```env
DAVEAGENT_API_KEY=your-azure-key
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_BASE_URL=https://your-resource.openai.azure.com/
```

#### Ollama (Local)

```env
DAVEAGENT_API_KEY=not-needed
DAVEAGENT_MODEL=llama2
DAVEAGENT_BASE_URL=http://localhost:11434/v1
```

#### Groq

```env
DAVEAGENT_API_KEY=gsk-your-groq-key
DAVEAGENT_MODEL=llama3-70b-8192
DAVEAGENT_BASE_URL=https://api.groq.com/openai/v1
```

---

## 🛡️ Configuración SSL

### Deshabilitar Verificación SSL

Para redes corporativas con certificados auto-firmados:

```env
DAVEAGENT_SSL_VERIFY=false
```

O usar argumento de línea de comandos:

```bash
daveagent --no-ssl-verify
```

### Usar Certificado Personalizado

```env
DAVEAGENT_CA_BUNDLE=/path/to/your/ca-bundle.crt
```

O configurar en `main.py`:

```python
import os
os.environ['REQUESTS_CA_BUNDLE'] = '/path/to/ca-bundle.crt'
```

---

## 🧠 Configuración de Memoria

### Directorio de Memoria

Por defecto: `.daveagent/memory/`

```env
DAVEAGENT_MEMORY_PATH=custom/path/to/memory
```

### Auto-Indexación

Indexar automáticamente al iniciar:

```env
DAVEAGENT_AUTO_INDEX=true
```

### Colecciones de Memoria

ChromaDB crea estas colecciones automáticamente:

| Colección | Propósito | Ejemplo |
|-----------|-----------|---------|
| `conversations` | Historial de conversaciones | Conversaciones pasadas |
| `codebase` | Código indexado | Archivos .py, .js, .md |
| `decisions` | Decisiones arquitectónicas | "Usamos PostgreSQL" |
| `preferences` | Preferencias del usuario | "Prefiero async/await" |
| `user_info` | Información del usuario | "Nombre: Juan, Rol: Backend Dev" |

---

## 📊 Configuración de Historial

### Límites de Tokens

```env
# Máximo de tokens en el historial
DAVEAGENT_MAX_TOKENS=8000

# Umbral para compresión automática
DAVEAGENT_SUMMARY_THRESHOLD=6000
```

En `main.py`:

```python
self.conversation_manager = ConversationManager(
    max_tokens=8000,
    summary_threshold=6000
)
```

### Comportamiento de Compresión

La compresión automática:
1. Se activa cuando `tokens > summary_threshold`
2. Crea un resumen con LLM
3. Mantiene últimos 3 mensajes + resumen
4. Reduce uso de tokens significativamente

---

## 🎨 Configuración de CLI

### Nivel de Logging

```env
DAVEAGENT_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Directorio de Logs

```env
DAVEAGENT_LOG_PATH=logs/
```

### Deshabilitar Colores

```env
DAVEAGENT_NO_COLOR=true
```

### Modo Debug

```bash
# Argumento de línea de comandos
daveagent --debug

# Variable de entorno
DAVEAGENT_DEBUG=true
```

---

## 🤖 Configuración de Agentes

### Temperatura del Modelo

```env
DAVEAGENT_TEMPERATURE=0.7  # 0.0 (determinista) a 1.0 (creativo)
```

En `main.py`:

```python
self.model_client = OpenAIChatCompletionClient(
    model="your-model",
    temperature=0.7,  # Ajustar aquí
    # ...
)
```

### Max Tokens por Respuesta

```env
DAVEAGENT_MAX_COMPLETION_TOKENS=4000
```

### Top P (Nucleus Sampling)

```env
DAVEAGENT_TOP_P=0.9
```

---

## 🔧 Configuración Avanzada

### Editar `main.py` Directamente

Para configuraciones más avanzadas, edita `src/main.py`:

```python
class DaveAgent:
    def __init__(self):
        # ========== Model Configuration ==========
        self.model_client = OpenAIChatCompletionClient(
            model=os.getenv("DAVEAGENT_MODEL", "deepseek-chat"),
            base_url=os.getenv("DAVEAGENT_BASE_URL", "https://api.deepseek.com/v1"),
            api_key=os.getenv("DAVEAGENT_API_KEY"),
            temperature=float(os.getenv("DAVEAGENT_TEMPERATURE", "0.7")),
            model_capabilities={
                "vision": True,
                "function_calling": True,
                "json_output": True,
            },
        )
        
        # ========== Conversation Configuration ==========
        self.conversation_manager = ConversationManager(
            max_tokens=int(os.getenv("DAVEAGENT_MAX_TOKENS", "8000")),
            summary_threshold=int(os.getenv("DAVEAGENT_SUMMARY_THRESHOLD", "6000"))
        )
        
        # ========== Memory Configuration ==========
        self.memory_manager = MemoryManager(
            persist_directory=os.getenv("DAVEAGENT_MEMORY_PATH", ".daveagent/memory")
        )
```

---

## 📝 Configuración de Prompts

Los prompts del sistema están centralizados en `src/config/prompts.py`.

### Modificar Prompt del Coder

Edita `src/config/prompts.py`:

```python
AGENT_SYSTEM_PROMPT = r"""
You are a powerful agentic AI coding assistant.
[Personaliza este prompt según tus necesidades]
...
"""
```

### Modificar Prompt del CodeSearcher

```python
CODE_SEARCHER_SYSTEM_MESSAGE = """
You are an expert code analyst specialized in SEARCH and ANALYSIS ONLY.
[Personaliza aquí]
...
"""
```

### Agregar Instrucciones Personalizadas

Agrega al final del prompt:

```python
AGENT_SYSTEM_PROMPT = r"""
[... prompt existente ...]

CUSTOM INSTRUCTIONS:
- Always use type hints in Python
- Prefer async/await over callbacks
- Add comprehensive docstrings
- Write tests for new functions
"""
```

---

## 🌐 Configuración de Network

### Proxy HTTP/HTTPS

```env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1
```

### Timeout de Requests

En `main.py`:

```python
import httpx

self.http_client = httpx.Client(
    timeout=30.0,  # 30 segundos
    # ...
)
```

---

## 📍 Configuración por Proyecto

Puedes tener configuraciones diferentes por proyecto creando `.env` en cada directorio:

```
~/project1/
  ├── .env  # Configuración para project1
  └── ...

~/project2/
  ├── .env  # Configuración para project2
  └── ...
```

CodeAgent usa automáticamente el `.env` del directorio actual.

---

## 🎯 Configuración Recomendada

### Para Desarrollo

```env
DAVEAGENT_API_KEY=your-key
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_LOG_LEVEL=DEBUG
DAVEAGENT_TEMPERATURE=0.7
DAVEAGENT_AUTO_INDEX=true
```

### Para Producción

```env
DAVEAGENT_API_KEY=your-key
DAVEAGENT_MODEL=gpt-4-turbo
DAVEAGENT_LOG_LEVEL=INFO  
DAVEAGENT_TEMPERATURE=0.5
DAVEAGENT_SSL_VERIFY=true
```

### Para Testing

```env
DAVEAGENT_MODEL=gpt-3.5-turbo
DAVEAGENT_TEMPERATURE=0.0  # Determinista
DAVEAGENT_LOG_LEVEL=ERROR
```

---

## 🔐 Seguridad

### Proteger API Keys

**NUNCA** incluyas API keys en el código fuente. Usa variables de entorno:

```bash
# Mal ❌
api_key = "sk-1234567890"

# Bien ✅
api_key = os.getenv("DAVEAGENT_API_KEY")
```

### .gitignore

Asegúrate de que `.env` esté en `.gitignore`:

```gitignore
.env
.env.local
.daveagent/
logs/
*.log
```

---

## 🔄 Variables de Entorno Completas

```env
# ==================== API ====================
DAVEAGENT_API_KEY=
DAVEAGENT_MODEL=deepseek-chat
DAVEAGENT_BASE_URL=https://api.deepseek.com/v1
DAVEAGENT_TEMPERATURE=0.7
DAVEAGENT_MAX_COMPLETION_TOKENS=4000
DAVEAGENT_TOP_P=0.9

# ==================== SSL ====================
DAVEAGENT_SSL_VERIFY=true
DAVEAGENT_CA_BUNDLE=

# ==================== Memory ====================
DAVEAGENT_MEMORY_PATH=.daveagent/memory
DAVEAGENT_AUTO_INDEX=false

# ==================== Logging ====================
DAVEAGENT_LOG_LEVEL=INFO
DAVEAGENT_LOG_PATH=logs/
DAVEAGENT_DEBUG=false
DAVEAGENT_NO_COLOR=false

# ==================== Conversation ====================
DAVEAGENT_MAX_TOKENS=8000
DAVEAGENT_SUMMARY_THRESHOLD=6000

# ==================== Proxy ====================
HTTP_PROXY=
HTTPS_PROXY=
NO_PROXY=

# ==================== Langfuse (Observability) ====================
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 📚 Ver También

- **[Installation](Installation)** - Instalación inicial
- **[Usage Guide](Usage-Guide)** - Cómo usar CodeAgent
- **[Troubleshooting](Troubleshooting)** - Solución de problemas
- **[Development](Development)** - Desarrollo y contribución

---

[← Volver al Home](Home) | [Solución de Problemas →](Troubleshooting)
