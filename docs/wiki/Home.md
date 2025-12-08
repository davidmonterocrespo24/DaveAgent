# CodeAgent (DaveAgent) - Wiki

Welcome to the official documentation for **CodeAgent** (also known as DaveAgent)!

CodeAgent is an AI-powered coding assistant that works in your current directory. It uses AutoGen 0.4 to orchestrate specialized agents that help you with development tasks.

## Documentation Index

### For Users

- **[Installation](Installation)** - Complete installation and setup guide
- **[Quick Start](Quick-Start)** - Get started with CodeAgent in 5 minutes
- **[Usage Guide](Usage-Guide)** - Commands, features, and workflows
- **[Available Tools](Tools-and-Features)** - Complete catalog of 45+ tools
- **[Memory System](Memory-System)** - Persistent vector memory with ChromaDB
- **[Configuration](Configuration)** - Customization and environment variables
- **[Troubleshooting](Troubleshooting)** - Common issues and solutions

### For Developers

- **[Architecture](Architecture)** - Project structure and components
- **[Development](Development)** - Contributing guide
- **[SWE-bench Evaluation](SWE-Bench-Evaluation)** - Evaluation with standard benchmarks
- **[API Reference](API-Reference)** - API and tools documentation

### Special Features

- **[CodeSearcher](CodeSearcher)** - Specialized code search agent
- **[File Mentions](File-Mentions)** - Mention files with @ for maximum priority
- **[RAG Memory](RAG-Memory)** - Persistent vector memory system
- **[Interactive CLI](CLI-Interface)** - Rich interface with colors and autocomplete

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Global Command** | Use `daveagent` from any directory |
| **Contextual Work** | Operates in your current directory automatically |
| **Vector Memory** | Remembers conversations, code, and decisions between sessions |
| **CodeSearcher** | Specialized agent for code search and analysis |
| **File Mentions** | Mention specific files with `@` for maximum priority |
| **45+ Tools** | Full integration: Filesystem, Git, JSON, CSV, Web, Memory |
| **Intelligent Agents** | Automatic selection of appropriate agent |
| **Complete Logging** | Detailed logging system for debugging |
| **Rich Interface** | CLI with colors and formatting using Rich |
| **Real-time Visualization** | See agent thoughts and actions while it works |

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# Install in development mode
pip install -e .

# Use from any directory
daveagent
```

### First Use

```bash
# Navigate to your project
cd my-project

# Start CodeAgent
daveagent

# Search code before modifying
You: /search authentication system

# Mention specific files with @
You: @main.py fix the authentication bug in this file

# Or simply ask what you need
You: create a REST API with FastAPI for user management
```

---

## Use Cases

### Software Development
```bash
cd my-project
daveagent

# Search before modifying
You: /search current authentication system

# Mention specific files
You: @main.py fix the authentication bug
You: @config.py @.env update the API configuration

# Modify with context
You: create an authentication module with JWT
You: refactor the code in services/ to use async/await
```

### Data Analysis
```bash
cd data-project
daveagent

You: read the sales.csv file and show a summary
You: combine all CSVs in the data/ folder
You: convert the configuration JSON to CSV
```

### Git Operations
```bash
cd my-repo
daveagent

You: commit the changes with a descriptive message
You: show the diff of the last 3 commits
You: create a branch feature/new-functionality
```

---

## Internal Commands

Within CodeAgent, you can use these commands:

| Command | Description |
|---------|-------------|
| `/help` | Show command help |
| `/search <query>` | Search and analyze code |
| `/index` | Index project in vector memory |
| `/memory` | Show memory statistics |
| `@<file>` | Mention specific file with high priority |
| `/debug` | Enable/disable debug mode |
| `/logs` | Show logs location |
| `/stats` | Show statistics |
| `/clear` | Clear history |
| `/new` | New conversation |
| `/exit` | Exit CodeAgent |

---

## Tool Categories

CodeAgent includes **45+ tools** organized in categories:

- **Filesystem** (7 tools) - File operations
- **Git** (8 tools) - Complete version control
- **JSON** (8 tools) - JSON processing and validation
- **CSV** (7 tools) - CSV analysis and manipulation
- **Web** (7 tools) - Wikipedia and web search
- **Analysis** (5 tools) - Code analysis and search
- **Memory** (8 tools) - RAG vector memory system

For more details, see **[Tools and Features](Tools-and-Features)**.

---

## Simplified Architecture

```
CodeAgent/
 src/
    agents/          # Specialized agents
       task_planner.py
       task_executor.py
       code_searcher.py
    config/          # Configuration and prompts
    interfaces/      # CLI interface
    managers/        # Conversation management
    memory/          # Vector memory system
    tools/           # 45+ tools
       filesystem/
       git/
       data/
       web/
       analysis/
    cli.py           # CLI entry point
 eval/                # SWE-bench evaluation
 docs/                # Documentation
 main.py              # Main application
```

For more details, see **[Architecture](Architecture)**.

---

## Contact and Community

- **Discord**: [Join our server](https://discord.gg/2dRTd4Cv)
- **GitHub**: https://github.com/davidmonterocrespo24/DaveAgent
- **Issues**: https://github.com/davidmonterocrespo24/DaveAgent/issues
- **Email**: contact@daveagent.ai

### Join our Discord Community

We invite you to join our Discord server to:
- Get help and support
- Report bugs and issues  
- Suggest new features
- Collaborate with other users
- Stay updated on news

**[Click here to join: https://discord.gg/2dRTd4Cv](https://discord.gg/2dRTd4Cv)**

---

## License

This project is under the MIT License. See [LICENSE](https://github.com/davidmonterocrespo24/DaveAgent/blob/main/LICENSE) for more details.

---

## Acknowledgments

- [AutoGen](https://microsoft.github.io/autogen/) - Agent framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/) - Interactive CLI
- [ChromaDB](https://www.trychroma.com/) - Vector database

---

Made with love using [AutoGen 0.4](https://microsoft.github.io/autogen/)
