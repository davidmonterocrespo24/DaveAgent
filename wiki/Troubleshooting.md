#  Troubleshooting - CodeAgent

This guide will help you resolve common issues when using CodeAgent.

##  Index

- [Installation Problems](#-installation-problems)
- [Configuration Problems](#-configuration-problems)
- [Connection Problems](#-connection-problems)
- [Tool Problems](#-tool-problems)
- [Memory Problems](#-memory-problems)
- [Performance Problems](#-performance-problems)
- [Logs and Debugging](#-logs-and-debugging)

---

##  Installation Problems

### "Command 'daveagent' not found"

**Problem**: The `daveagent` command is not found after installation.

**Solutions**:

```bash
# Solution 1: Reinstall
cd DaveAgent
pip install -e .

# Solution 2: Verify installation
pip show daveagent-cli

# Solution 3: Use module directly
python -m src.cli

# Solution 4: Add pip to PATH
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
# Or add to .bashrc / .zshrc
```

**Windows specific**:
```powershell
# Check Scripts PATH
python -m site --user-site
# Add ...\Python\Scripts to system PATH
```

### "ModuleNotFoundError: No module named 'autogen'"

**Problem**: AutoGen or dependencies are missing.

**Solutions**:

```bash
# Solution 1: Install dependencies
pip install -r requirements.txt

# Solution 2: Install AutoGen manually
pip install 'autogen-agentchat>=0.4.0' 'autogen-ext[openai]>=0.4.0'

# Solution 3: Verify Python version
python --version  # Must be 3.10+

# Solution 4: Reinstall in clean virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
pip install -e .
```

### "Permission denied" on Linux/macOS

**Problem**: You don't have permissions to install globally.

**Solutions**:

```bash
# Solution 1: Install for user only
pip install --user -e .

# Solution 2: Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install -e .

# Solution 3: Use sudo (not recommended)
sudo pip install -e .
```

---

##  Configuration Problems

### "API key not found"

**Problem**: API key not found.

**Solutions**:

```bash
# Solution 1: Create .env file
cd DaveAgent
touch .env
echo "DAVEAGENT_API_KEY=your-key-here" >> .env

# Solution 2: System environment variable
export DAVEAGENT_API_KEY=your-key  # Linux/macOS
set DAVEAGENT_API_KEY=your-key     # Windows CMD
$env:DAVEAGENT_API_KEY="your-key"  # Windows PowerShell

# Solution 3: Edit main.py directly
# Edit src/main.py and add the API key
```

### "Invalid model name"

**Problem**: The specified model doesn't exist or isn't available.

**Solutions**:

```env
# Check available models by provider

# DeepSeek
DAVEAGENT_MODEL=deepseek-chat

# OpenAI
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_MODEL=gpt-4-turbo
DAVEAGENT_MODEL=gpt-3.5-turbo

# Groq
DAVEAGENT_MODEL=llama3-70b-8192
DAVEAGENT_MODEL=mixtral-8x7b-32768
```

---

##  Connection Problems

### "SSL Certificate Error"

**Problem**: SSL certificate errors in corporate networks.

**Solutions**:

```bash
# Solution 1: Disable SSL verification (development)
daveagent --no-ssl-verify

# Solution 2: Environment variable
export DAVEAGENT_SSL_VERIFY=false

#Solution 3: Use corporate certificate
export REQUESTS_CA_BUNDLE=/path/to/company-ca.crt

# Solution 4: Configure in .env
echo "DAVEAGENT_SSL_VERIFY=false" >> .env
```

**Warning**: Only disable SSL in development/trusted environments.

### "Connection Refused" or "Timeout"

**Problem**: Cannot connect to API endpoint.

**Solutions**:

```bash
# Verify connectivity
curl -I https://api.deepseek.com/v1
ping api.openai.com

# Check proxy configuration
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Configure proxy if necessary
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080

# Check firewall
# Ensure port 443 is open
```

### "Rate Limit Exceeded"

**Problem**: You've exceeded the API rate limit.

**Solutions**:

```bash
# Solution 1: Wait before retrying
# Most APIs have per-minute limits

# Solution 2: Use model with higher limit
# Switch to paid plan or higher tier

# Solution 3: Implement retry with backoff
# Edit src/main.py to add retry logic
```

---

##  Tool Problems

### "Tool execution failed"

**Problem**: A tool failed to execute.

**Diagnosis**:

```bash
# Enable debug mode
daveagent --debug

# Check logs
tail -f logs/daveagent_*.log

# Verify file permissions
ls -la problem-file.py
```

**Common solutions**:

```bash
# For file tools
chmod +r file.py  # Give read permissions
chmod +w file.py  # Give write permissions

# For Git tools
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# For CSV/JSON tools
# Check file encoding
file -I data.csv
```

### "edit_file cannot find the string"

**Problem**: `edit_file` cannot find the text to replace.

**Solutions**:

```bash
# The issue is usually whitespace or exact differences

# Solution 1: Read the file first
You: read auth.py lines 40-50
# Then copy the EXACT text shown

# Solution 2: Use @mention for context
You: @auth.py change line 45 from X to Y

# Solution 3: Be more specific
You: in auth.py, find the login function and add error handling
# Instead of: edit line 45
```

### "Git command failed"

**Problem**: Git commands fail.

**Solutions**:

```bash
# Verify you're in a Git repository
git status

# Initialize repo if necessary
git init

# Configure Git user
git config user.name "Your Name"
git config user.email "you@example.com"

# Check remote
git remote -v

# If no remote, add it
git remote add origin https://github.com/user/repo.git
```

---

##  Memory Problems

### "ChromaDB connection failed"

**Problem**: Cannot connect to ChromaDB.

**Solutions**:

```bash
# Solution 1: Delete and recreate database
rm -rf .daveagent/memory/
daveagent
You: /index  # Reindex

# Solution 2: Verify permissions
chmod -R 755 .daveagent/

# Solution 3: Reinstall ChromaDB
pip install --upgrade chromadb
```

### "/index fails or freezes"

**Problem**: Indexing takes too long or fails.

**Solutions**:

```bash
# Solution 1: Index specific directories
# Instead of /index, index only what's needed
You: index only the src/ directory

# Solution 2: Exclude large files
# Add to .gitignore:
*.log
*.db
node_modules/
__pycache__/

# Solution 3: Increase timeout (in main.py)
# Edit ChromaDB configuration

# Solution 4: Clean and reindex
rm -rf .daveagent/memory/
daveagent --debug
You: /index
```

### "Memory query returns no results"

**Problem**: Memory searches return no results.

**Solutions**:

```bash
# Solution 1: Verify project is indexed
You: /memory
# Should show collections with data

# Solution 2: Reindex
You: /index

# Solution 3: Use broader queries
# Instead of: "exact function name"
# Use: "function that handles authentication"

# Solution 4: Check logs for embedding errors
daveagent --debug
# Search for "embedding" errors
```

---

##  Performance Problems

### "CodeAgent is very slow"

**Problem**: Responses take too long.

**Solutions**:

```bash
# Solution 1: Use faster model
DAVEAGENT_MODEL=gpt-3.5-turbo
# Or: deepseek-coder

# Solution 2: Reduce context
DAVEAGENT_MAX_TOKENS=4000
DAVEAGENT_SUMMARY_THRESHOLD=3000

# Solution 3: Clear history frequently
You: /clear

# Solution 4: Disable memory if not using it
# Comment out memory tools in main.py
```

### "Uses too many tokens"

**Problem**: Excessive token consumption.

**Solutions**:

```bash
# Solution 1: Compress history more frequently
DAVEAGENT_SUMMARY_THRESHOLD=4000  # Reduce from 6000

# Solution 2: Clear history manually
You: /clear

# Solution 3: Be more specific in requests
# Bad: "do something with this project"
# Good: "add error handling to login function in auth.py"

# Solution 4: Use file mentions
You: @auth.py fix the bug
# Instead of letting the agent search
```

### "Out of Memory"

**Problem**: Python runs out of memory.

**Solutions**:

```bash
# Solution 1: Close and restart CodeAgent
# Ctrl+C, then daveagent

# Solution 2: Clean ChromaDB memory
rm -rf .daveagent/memory/chroma.sqlite3

# Solution 3: Increase Python memory (in main.py)
# Only for very large projects

# Solution 4: Exclude large files from indexing
# Use .gitignore to exclude:
*.db
*.sqlite
large_data/
```

---

##  Logs and Debugging

### Enable Debug Mode

```bash
# Method 1: CLI argument
daveagent --debug

# Method 2: Environment variable
export DAVEAGENT_DEBUG=true
daveagent

# Method 3: In .env
DAVEAGENT_DEBUG=true
DAVEAGENT_LOG_LEVEL=DEBUG
```

### Log Location

```bash
# Default in  logs/ directory
ls -la logs/

# View most recent log
tail -f logs/daveagent_$(date +%Y%m%d)*.log

# Search errors
grep -i "error" logs/*

# Search warnings
grep -i "warning" logs/*
```

### View Specific Log

```bash
# Inside CodeAgent
You: /logs

# Result:
 Log file: logs/daveagent_20240315_143022.log

# Then view with:
tail -f logs/daveagent_20240315_143022.log
```

### Useful Debug Information

When reporting a problem, include:

```bash
# 1. CodeAgent version
daveagent --version

# 2. Python version
python --version

# 3. Operating system
uname -a  # Linux/macOS
systeminfo  # Windows

# 4. Installed dependencies
pip list | grep -E "autogen|rich|prompt"

# 5. Last log lines
tail -n 50 logs/daveagent_*.log

# 6. Environment variables (without API keys)
env | grep DAVEAGENT
```

---

##  Getting Help

### Support Resources

1. **Discord** (Recommended for quick responses)
   - [Join the server](https://discord.gg/2dRTd4Cv)
   - #support channel for help
   - #bugs channel for bug reports

2. **GitHub Issues**
   - [Create issue](https://github.com/davidmonterocrespo24/DaveAgent/issues)
   - Search similar issues first
   - Use bug report template

3. **Email**
   - contact@daveagent.ai
   - Include logs and details

### Bug Report Template

When reporting a problem, include:

```markdown
**Problem**:
[Brief problem description]

**Steps to Reproduce**:
1. Run command X
2. Do Y
3. See error Z

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Environment**:
- OS: [Windows 11 / Ubuntu 22.04 / macOS 14]
- Python: [3.10.5]
- CodeAgent: [1.1.0]
- Model: [gpt-4]

**Logs**:
```
[Paste last 20-30 lines of log]
```

**Configuration .env (without API keys)**:
```
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_SSL_VERIFY=false
...
```
```

---

##  Troubleshooting Checklist

Before reporting a bug, verify:

- [ ] CodeAgent is updated (`git pull`, `pip install -e .`)
- [ ] Python is 3.10+ (`python --version`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] API key configured (`cat .env`)
- [ ] Logs reviewed (`tail logs/*.log`)
- [ ] Debug mode enabled (`daveagent --debug`)
- [ ] Problem is reproducible
- [ ] Searched existing issues

---

##  See Also

- **[Configuration](Configuration)** - Configuration options
- **[Installation](Installation)** - Installation guide
- **[Development](Development)** - Contribute to the project
- **[GitHub Issues](https://github.com/davidmonterocrespo24/DaveAgent/issues)** - Known issues

---

[← Back to Home](Home) | [Configuration →](Configuration)
