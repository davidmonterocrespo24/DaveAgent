#  Configuration - CodeAgent

This guide documents all available configuration options to customize CodeAgent.

##  Configuration Files

### 1. `.env` - Environment Variables

Create a `.env` file in the project root directory:

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

##  API Configuration

### Supported Providers

CodeAgent supports any OpenAI-compatible API provider.

#### DeepSeek (Default)

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

##  SSL Configuration

### Disable SSL Verification

For corporate networks with self-signed certificates:

```env
DAVEAGENT_SSL_VERIFY=false
```

Or use command line argument:

```bash
daveagent --no-ssl-verify
```

### Use Custom Certificate

```env
DAVEAGENT_CA_BUNDLE=/path/to/your/ca-bundle.crt
```

Or configure in `main.py`:

```python
import os
os.environ['REQUESTS_CA_BUNDLE'] = '/path/to/ca-bundle.crt'
```

---

##  Memory Configuration

### Memory Directory

Default: `.daveagent/memory/`

```env
DAVEAGENT_MEMORY_PATH=custom/path/to/memory
```

### Auto-Indexing

Automatically index on start:

```env
DAVEAGENT_AUTO_INDEX=true
```

### Memory Collections

ChromaDB creates these collections automatically:

| Collection | Purpose | Example |
|------------|---------|---------|
| `conversations` | Conversation history | Past conversations |
| `codebase` | Indexed code | .py, .js, .md files |
| `decisions` | Architectural decisions | "We use PostgreSQL" |
| `preferences` | User preferences | "Prefer async/await" |
| `user_info` | User information | "Name: John, Role: Backend Dev" |

---

##  History Configuration

### Token Limits

```env
# Maximum tokens in history
DAVEAGENT_MAX_TOKENS=8000

# Threshold for automatic compression
DAVEAGENT_SUMMARY_THRESHOLD=6000
```

In `main.py`:

```python
self.conversation_manager = ConversationManager(
    max_tokens=8000,
    summary_threshold=6000
)
```

### Compression Behavior

Automatic compression:
1. Activates when `tokens > summary_threshold`
2. Creates summary with LLM
3. Keeps last 3 messages + summary
4. Significantly reduces token usage

---

##  CLI Configuration

### Logging Level

```env
DAVEAGENT_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Logs Directory

```env
DAVEAGENT_LOG_PATH=logs/
```

### Disable Colors

```env
DAVEAGENT_NO_COLOR=true
```

### Debug Mode

```bash
# Command line argument
daveagent --debug

# Environment variable
DAVEAGENT_DEBUG=true
```

---

##  Agent Configuration

### Model Temperature

```env
DAVEAGENT_TEMPERATURE=0.7  # 0.0 (deterministic) to 1.0 (creative)
```

In `main.py`:

```python
self.model_client = OpenAIChatCompletionClient(
    model="your-model",
    temperature=0.7,  # Adjust here
    # ...
)
```

### Max Tokens per Response

```env
DAVEAGENT_MAX_COMPLETION_TOKENS=4000
```

### Top P (Nucleus Sampling)

```env
DAVEAGENT_TOP_P=0.9
```

---

##  Advanced Configuration

### Edit `main.py` Directly

For more advanced configurations, edit `src/main.py`:

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

##  Prompts Configuration

System prompts are centralized in `src/config/prompts.py`.

### Modify Coder Prompt

Edit `src/config/prompts.py`:

```python
AGENT_SYSTEM_PROMPT = r"""
You are a powerful agentic AI coding assistant.
[Customize this prompt for your needs]
...
"""
```

### Modify CodeSearcher Prompt

```python
CODE_SEARCHER_SYSTEM_MESSAGE = """
You are an expert code analyst specialized in SEARCH and ANALYSIS ONLY.
[Customize here]
...
"""
```

### Add Custom Instructions

Add at the end of the prompt:

```python
AGENT_SYSTEM_PROMPT = r"""
[... existing prompt ...]

CUSTOM INSTRUCTIONS:
- Always use type hints in Python
- Prefer async/await over callbacks
- Add comprehensive docstrings
- Write tests for new functions
"""
```

---

##  Network Configuration

### HTTP/HTTPS Proxy

```env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1
```

### Request Timeout

In `main.py`:

```python
import httpx

self.http_client = httpx.Client(
    timeout=30.0,  # 30 seconds
    # ...
)
```

---

##  Per-Project Configuration

You can have different configurations per project by creating `.env` in each directory:

```
~/project1/
   .env  # Configuration for project1
   ...

~/project2/
   .env  # Configuration for project2
   ...
```

CodeAgent automatically uses the `.env` from the current directory.

---

##  Recommended Configuration

### For Development

```env
DAVEAGENT_API_KEY=your-key
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_LOG_LEVEL=DEBUG
DAVEAGENT_TEMPERATURE=0.7
DAVEAGENT_AUTO_INDEX=true
```

### For Production

```env
DAVEAGENT_API_KEY=your-key
DAVEAGENT_MODEL=gpt-4-turbo
DAVEAGENT_LOG_LEVEL=INFO  
DAVEAGENT_TEMPERATURE=0.5
DAVEAGENT_SSL_VERIFY=true
```

### For Testing

```env
DAVEAGENT_MODEL=gpt-3.5-turbo
DAVEAGENT_TEMPERATURE=0.0  # Deterministic
DAVEAGENT_LOG_LEVEL=ERROR
```

---

##  Security

### Protect API Keys

**NEVER** include API keys in source code. Use environment variables:

```bash
# Bad 
api_key = "sk-1234567890"

# Good 
api_key = os.getenv("DAVEAGENT_API_KEY")
```

### .gitignore

Make sure `.env` is in `.gitignore`:

```gitignore
.env
.env.local
.daveagent/
logs/
*.log
```

---

##  Complete Environment Variables

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

##  See Also

- **[Installation](Installation)** - Initial installation
- **[Usage Guide](Usage-Guide)** - How to use CodeAgent
- **[Troubleshooting](Troubleshooting)** - Problem solving
- **[Development](Development)** - Development and contribution

---

[← Back to Home](Home) | [Troubleshooting →](Troubleshooting)
