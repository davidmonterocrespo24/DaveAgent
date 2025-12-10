# 🤖 DaveAgent - AI-Powered Coding Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AutoGen](https://img.shields.io/badge/powered%20by-AutoGen%200.4-orange.svg)](https://microsoft.github.io/autogen/)

DaveAgent is an intelligent AI-powered coding assistant that works in your current directory. It uses AutoGen 0.4 to orchestrate specialized agents that help you with development tasks.

## ✨ Features

- 🚀 **Global CLI Command**: Use `daveagent` from any directory
- 📂 **Contextual Work**: Operates in your current directory automatically
- 🧠 **Vector Memory with ChromaDB**: Remembers conversations, code, and decisions between sessions
- 🔍 **CodeSearcher**: Specialized agent for searching and analyzing code
- 📎 **File Mentions with @**: Mention specific files with `@` to give them maximum priority in context
- 🔧 **45+ Integrated Tools**: Filesystem, Git, JSON, CSV, Web, Memory (RAG), and more
- 🤖 **Intelligent Agents**: Automatic selection of the appropriate agent
- 📊 **Complete Logging**: Detailed logging system for debugging
- 🎨 **Rich Interface**: CLI with colors and formatting using Rich
- ⚡ **Real-time Visualization**: See the agent's thoughts and actions while it works

## 🎯 Use Cases

### Software Development
```bash
cd my-project
daveagent

# Search code before modifying
You: /search current authentication system

# Mention specific files with @
You: @main.py fix the authentication bug in this file
You: @config.py @.env update the API configuration

# Modify with context
You: create an authentication module with JWT
You: refactor the code in services/ to use async/await
You: find all TODOs in the project
```

## 📦 Installation

### Installation from PyPI (Coming Soon)

**When published on PyPI**:

```bash
pip install daveagent-ai
daveagent
```

### Installation from Source Code

```bash
# 1. Clone or download the project
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# 2. Install in development mode
pip install -e .

# 3. Use from any directory!
daveagent
```

### Requirements

- Python 3.10 or higher
- pip (Python package manager)

### Main Dependencies

- `autogen-agentchat>=0.4.0` - Agent framework
- `autogen-ext[openai]>=0.4.0` - Model extensions
- `prompt-toolkit>=3.0.0` - Command-line interface
- `rich>=13.0.0` - Formatting and colors
- `pandas>=2.0.0` - Data processing

See [INSTALACION.md](INSTALACION.md) for detailed instructions.

## 🚀 Usage

### Basic Command

```bash
# From any directory
cd your-project
daveagent
```

### Options

```bash
# Debug mode (detailed logs)
daveagent --debug

# View version
daveagent --version

# View help
daveagent --help
```

### Internal Commands

Within DaveAgent, you can use these commands:

| Command | Description |
|---------|-------------|
| `/help` | Show command help |
| `/search <query>` | 🔍 Search and analyze code |
| `/index` | 🧠 Index project in vector memory |
| `/memory` | 📊 Show memory statistics |
| `@<file>` | 📎 Mention specific file with high priority |
| `/debug` | Enable/disable debug mode |
| `/logs` | Show logs location |
| `/stats` | Show statistics |
| `/clear` | Clear history |
| `/new` | New conversation |
| `/exit` | Exit DaveAgent |

#### 🔍 /search Command

The `/search` command invokes the **CodeSearcher** agent to search and analyze code:

```bash
You: /search authentication function
You: /search where is the TaskPlanner class used
You: /search how does the logging system work
```

**CodeSearcher provides you with:**
- 📍 Relevant files with exact locations
- 🔧 Functions found with complete code
- 📦 Important variables and constants
- 🔗 Dependencies between components
- 💡 Recommendations on what to modify

See [docs/CODESEARCHER_GUIDE.md](docs/CODESEARCHER_GUIDE.md) for more details.

#### 📎 File Mentions with @

Mention specific files in your query using `@`:

```bash
You: @main.py explain how this file works
You: @config.py @.env update the database connection settings
You: @src/agents/code_searcher.py add docstrings to all methods
```

## 📖 Examples

### Example 1: Use CodeSearcher before modifying

```bash
cd my-project
daveagent

# First, search for context
You: /search existing utilities system

# The agent shows functions, files and current structure
# Now modify with context

You: create a utils.py module with functions for:
    - validate email
    - format dates
    - calculate MD5 hash
```

DaveAgent first analyzes the existing code and then creates the `my-project/utils.py` file with the requested functions, avoiding duplicates and maintaining consistency.

### Example 2: Analyze a Project

```bash
cd existing-project
daveagent

You: analyze the project structure and give me a summary
You: how many functions are there in total?
You: find all files that use the requests library
```

### Example 3: Data Operations

```bash
cd data
daveagent

You: read the sales.csv file and show the top 10 sales
You: create a new CSV with only 2024 sales
You: convert the config.json file to CSV
```

## 🐛 Debugging and Logs

### View Logs

```bash
# Start with detailed logs
daveagent --debug

# Within DaveAgent
You: /logs
📄 Log file: logs/daveagent_20250131_154022.log
```

### Log Location

Logs are saved in:
```
logs/
└── daveagent_YYYYMMDD_HHMMSS.log
```

Each file contains detailed logs with format:
```
2025-01-31 15:40:22 | DaveAgent | INFO | process_user_request:257 | 📝 New request...
```

## 🏗️ Architecture

```
DaveAgent/
├── src/
│   ├── agents/          # Specialized agents
│   │   ├── task_planner.py      # Task planning
│   │   ├── task_executor.py     # Task execution
│   │   └── code_searcher.py     # 🔍 Code search
│   ├── config/          # Configuration and prompts
│   ├── interfaces/      # CLI interface
│   ├── managers/        # Conversation management
│   ├── tools/           # 45+ tools
│   │   ├── filesystem/
│   │   ├── git/
│   │   ├── data/       # JSON, CSV
│   │   ├── web/        # Wikipedia, web search
│   │   └── analysis/   # Code analysis, grep, terminal
│   ├── utils/          # Utilities (logger)
│   └── cli.py          # CLI entry point
├── docs/               # Documentation
│   └── CODESEARCHER_GUIDE.md  # CodeSearcher Guide
└── main.py             # Main application
```

## 🔧 Configuration

### API Key

DaveAgent uses DeepSeek by default. To change the model:

1. Edit `main.py`:
```python
self.model_client = OpenAIChatCompletionClient(
    model="gpt-4",  # Change here
    api_key="your-api-key",
    # ...
)
```

2. Or use environment variables in `.daveagent/.env`:
```bash
DAVEAGENT_API_KEY=your-api-key
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_BASE_URL=https://api.openai.com/v1
```

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a branch: `git checkout -b feature/new-functionality`
3. Commit your changes: `git commit -m 'Add new functionality'`
4. Push to the branch: `git push origin feature/new-functionality`
5. Open a Pull Request

### Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Check types
mypy src/
```

## 📚 Documentation

### User Guides
- [Installation Guide](INSTALACION.md) - Detailed installation
- [CodeSearcher Guide](docs/CODESEARCHER_GUIDE.md) - 🔍 Code search and analysis
- [File Mentions Guide](docs/FILE_MENTIONS.md) - 📎 Mention files with @
- [Logging Guide](LOGGING_GUIDE.md) - Logging system

## 🧪 Evaluation with SWE-bench (Linux)

To evaluate the agent's performance using the **SWE-bench Verified** standard, we have included an automated script that works in Linux environments (or WSL2).

### Prerequisites
- Linux or WSL2 environment
- Docker installed and running (required for evaluation harness)
- Python 3.10+

### Execution

The `setup_and_run_linux.sh` script automates the entire process:
1. Compiles and installs the agent
2. Runs inference on 10 test tasks
3. Runs the official evaluation using Docker

```bash
# 1. Grant execution permissions
chmod +x setup_and_run_linux.sh

# 2. Run the script
./setup_and_run_linux.sh
```

**Note:** The complete evaluation may take time depending on your connection speed and CPU.

## 📝 License

This project is under the MIT License. See [LICENSE](LICENSE) for more details.

##  Contact & Community

- **Discord Community**: [Join our Discord server](https://discord.gg/2dRTd4Cv) - Get help, report bugs, suggest improvements, and collaborate with other users
- **GitHub**: https://github.com/davidmonterocrespo24/DaveAgent
- **Issues**: https://github.com/davidmonterocrespo24/DaveAgent/issues
- **Email**: davidmonterocrespo24@gmail.com

### Join Our Discord Community

We encourage you to join our Discord server to:
- 💬 **Get Help**: Ask questions and get support from the community
- 🐛 **Report Bugs**: Help us improve by reporting issues you encounter
- 💡 **Suggest Features**: Share your ideas for new features and improvements
- 🤝 **Collaborate**: Connect with other users and contributors
- 📢 **Stay Updated**: Get the latest news and updates about DaveAgent

**[Click here to join: https://discord.gg/2dRTd4Cv](https://discord.gg/2dRTd4Cv)**

