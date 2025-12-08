#  CodeAgent Installation

This guide will take you through the complete installation process of CodeAgent on your system.

##  Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **pip**: Python package manager
- **Git**: To clone the repository (optional if you download ZIP)
- **Operating System**: Windows, Linux, macOS

### Verify Python

```bash
python --version
# Should show: Python 3.10.x or higher

pip --version
# Should show pip version
```

If you don't have Python 3.10+, download it from [python.org](https://www.python.org/downloads/)

---

##  Method 1: Installation from Source Code (Recommended)

### Step 1: Clone the Repository

```bash
# Option A: Clone with HTTPS
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# Option B: Clone with SSH
git clone git@github.com:davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# Option C: Download ZIP
# Download from GitHub and extract, then:
cd DaveAgent
```

### Step 2: Install in Development Mode

```bash
# Install package in editable mode
pip install -e .

# This installs:
# - CodeAgent and all its dependencies
# - The 'daveagent' global command
# - Allows editing code without reinstalling
```

### Step 3: Verify Installation

```bash
# Verify command is available
daveagent --version

# Should show something like:
# DaveAgent version 1.1.0
```

### Step 4: Ready to Use!

```bash
# Navigate to any directory
cd ~/my-project

# Start CodeAgent
daveagent
```

---

##  Method 2: Installation from PyPI (Coming Soon)

**Note**: This option will be available when published on PyPI.

```bash
# Simple installation (coming soon)
pip install daveagent-ai

# Use from any directory
daveagent
```

---

##  Installing Optional Dependencies

### Development Dependencies

If you plan to contribute to the project or develop features:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# This installs additional tools:
# - pytest (testing)
# - black (code formatting)
# - flake8 (linting)
# - mypy (type checking)
```

### Complete Dependencies

```bash
# View all installed dependencies
pip list | grep -E "autogen|rich|prompt|pandas"

# Main dependencies:
# - autogen-agentchat>=0.4.0     - Agent framework
# - autogen-ext[openai]>=0.4.0   - Model extensions
# - prompt-toolkit>=3.0.0         - CLI interface
# - rich>=13.0.0                  - Formatting and colors
# - pandas>=2.0.0                 - Data processing
# - wikipedia>=1.4.0              - Web tools
# - python-dotenv>=1.0.0          - Environment variables
# - chromadb>=0.4.0               - Vector database
```

---

##  Post-Installation Configuration

### 1. Configure API Key

CodeAgent uses DeepSeek by default, but you can use any OpenAI-compatible provider.

#### Method A: Environment Variables

Create a `.env` file in the working directory:

```bash
# In CodeAgent root directory
touch .env
```

Edit `.env` and add:

```env
# API Configuration
DAVEAGENT_API_KEY=your-api-key-here
DAVEAGENT_MODEL=deepseek-chat
DAVEAGENT_BASE_URL=https://api.deepseek.com/v1

# Or for OpenAI:
# DAVEAGENT_API_KEY=sk-...
# DAVEAGENT_MODEL=gpt-4
# DAVEAGENT_BASE_URL=https://api.openai.com/v1

# SSL Configuration (optional)
DAVEAGENT_SSL_VERIFY=true
```

#### Method B: Edit main.py Directly

Edit `src/main.py`:

```python
self.model_client = OpenAIChatCompletionClient(
    model="your-model",           # Change here
    base_url="your-base-url",      # Change here
    api_key="your-api-key",        # Change here
    model_capabilities={
        "vision": True,
        "function_calling": True,
        "json_output": True,
    },
)
```

### 2. SSL Configuration (Corporate Networks)

If you experience SSL certificate errors:

```bash
# Option 1: Environment variable in .env
DAVEAGENT_SSL_VERIFY=false

# Option 2: Command line argument
daveagent --no-ssl-verify

# Option 3: System variable
export DAVEAGENT_SSL_VERIFY=false  # Linux/macOS
set DAVEAGENT_SSL_VERIFY=false     # Windows CMD
$env:DAVEAGENT_SSL_VERIFY="false"  # Windows PowerShell
```

### 3. Configure Working Directory

By default, CodeAgent operates in the current directory:

```bash
# Navigate to project
cd ~/my-project

# Start CodeAgent (will work in ~/my-project)
daveagent
```

---

##  Linux-Specific Installation

### Ubuntu/Debian

```bash
# Install Python 3.10+ if not available
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip git

# Clone and install
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent
pip install -e .
```

### Fedora/RHEL

```bash
# Install dependencies
sudo dnf install python3.10 python3-pip git

# Clone and install
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent
pip install -e .
```

### Automated Installation Script

For Linux with SWE-bench evaluation:

```bash
# Grant execution permissions
chmod +x setup_and_run_linux.sh

# Run script (compiles, installs, and runs evaluation)
./setup_and_run_linux.sh
```

---

##  Windows-Specific Installation

### Windows 10/11

```powershell
# Verify Python (must be 3.10+)
python --version

# Clone repository
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# Install
pip install -e .

# Verify
daveagent --version
```

### Build and Install Script

```bash
# Use Windows script
.\build_and_install.bat
```

**Note for Windows**: If you encounter permission issues, run PowerShell as Administrator.

---

##  macOS-Specific Installation

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.10+
brew install python@3.10

# Clone and install
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent
pip3 install -e .

# Verify
daveagent --version
```

---

##  Docker Installation (Coming Soon)

```bash
# Build Docker image
docker build -t codeagent .

# Run container
docker run -it --rm \
  -v $(pwd):/workspace \
  -e DAVEAGENT_API_KEY=your-key \
  codeagent
```

---

##  Installation Verification

### Basic Test

```bash
# Start CodeAgent
daveagent

# Inside CodeAgent, test:
You: /help

# Should show command help
```

### Tool Test

```bash
You: read the README.md file
You: /search main function
You: git status
```

### Memory Test

```bash
You: /index
# Should index the project

You: /memory
# Should show memory statistics
```

---

##  Installation Troubleshooting

### Problem: "Command 'daveagent' not found"

**Solution**:
```bash
# Verify pip installed in correct PATH
pip show daveagent-cli

# Or use module directly
python -m src.cli
```

### Problem: "ModuleNotFoundError: No module named 'autogen'"

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install manually
pip install 'autogen-agentchat>=0.4.0' 'autogen-ext[openai]>=0.4.0'
```

### Problem: SSL Errors in Corporate Networks

**Solution**:
```bash
# Disable SSL verification
daveagent --no-ssl-verify

# Or configure corporate certificates
export REQUESTS_CA_BUNDLE=/path/to/your/ca-bundle.crt
```

### Problem: "Permission denied" on Linux/macOS

**Solution**:
```bash
# Install for current user only
pip install --user -e .

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# Or venv\Scripts\activate  # Windows
pip install -e .
```

---

##  Updating CodeAgent

### Update from Git

```bash
# Navigate to CodeAgent directory
cd DaveAgent

# Get latest changes
git pull origin main

# Reinstall (if there are dependency changes)
pip install -e .
```

### Update Dependencies

```bash
# Update all dependencies
pip install --upgrade -r requirements.txt

# Or update only AutoGen
pip install --upgrade 'autogen-agentchat>=0.4.0' 'autogen-ext[openai]>=0.4.0'
```

---

##  Uninstallation

```bash
# Uninstall package
pip uninstall daveagent-cli

# Remove directory (if cloned from Git)
rm -rf DaveAgent

# Clean configuration files (optional)
rm -rf ~/.daveagent
```

---

##  Next Steps

Once installed correctly:

1. **[Quick Start](Quick-Start)** - Learn basic commands in 5 minutes
2. **[Usage Guide](Usage-Guide)** - Workflows and use cases
3. **[Configuration](Configuration)** - Customize CodeAgent to your needs
4. **[Tools](Tools-and-Features)** - Explore the 45+ available tools

---

##  Need Help?

- **Discord**: [Join our server](https://discord.gg/2dRTd4Cv)
- **Issues**: [GitHub Issues](https://github.com/davidmonterocrespo24/DaveAgent/issues)
- **Email**: contact@daveagent.ai

---

[← Back to Home](Home) | [Configuration →](Configuration)
