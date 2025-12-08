# 🚀 Quick Start - CodeAgent

Learn to use CodeAgent in 5 minutes with this quick guide.

## ⚡ Express Installation

```bash
# Clone and install
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent
pip install -e .

# Verify
daveagent --version
```

**Problems?** Go to the [Complete Installation Guide](Installation).

---

## 🎯 First Use

### 1. Start CodeAgent

```bash
# Navigate to your project
cd ~/my-project

# Start the agent
daveagent
```

You'll see a banner like this:

```
╔══════════════════════════════════════════════════════╗
║            🤖 D A V E A G E N T  v1.1.0             ║
║         AI-Powered Coding Assistant                  ║
╚══════════════════════════════════════════════════════╝

Working in: /home/user/my-project
Type '/help' for commands, '/exit' to quit

You: 
```

### 2. Basic Commands

```bash
# View help
You: /help

# Read a file
You: read the README.md file

# Search in code
You: /search authentication function

# View Git status
You: git status
```

### 3. Exit

```bash
You: /exit
# or Ctrl+C
```

---

## 📝 Essential Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show help | `You: /help` |
| `/search <query>` | Search code | `You: /search login function` |
| `/index` | Index project in memory | `You: /index` |
| `/memory` | View memory statistics | `You: /memory` |
| `@<file>` | Mention file with priority | `You: @main.py explain this` |
| `/new` | New conversation | `You: /new` |
| `/exit` | Exit | `You: /exit` |

---

## 🎓 5-Minute Tutorial

### Example 1: Read and Explain Code

```bash
You: read the main.py file and explain what it does

# The agent will read the file and provide an explanation
```

### Example 2: Search Code

```bash
You: /search authentication logic

# CodeSearcher will search and show where authentication is
# Result:
# 📍 Files Found:
# - auth.py:45-67 - Login function with JWT
# - middleware.py:23-34 - Auth middleware
```

### Example 3: Create a New File

```bash
You: create a new file utils.py with a function to validate email addresses

# The agent will create utils.py with:
# - validate_email() function
# - Regex for validation
# - Docstrings
# - Error handling
```

### Example 4: Modify Existing Code

```bash
You: @auth.py add error handling to the login function

# The agent:
# 1. Reads auth.py
# 2. Identifies the login function
# 3. Adds try-except
# 4. Shows changes made
```

### Example 5: Git Operations

```bash
You: show me the git status

# CodeAgent executes: git status

You: commit the changes with message "Added email validation"

# CodeAgent executes:
# - git add .
# - git commit -m "Added email validation"
```

---

## 💡 Common Use Cases

### Web Development

```bash
cd my-web-app
daveagent

You: create a FastAPI endpoint for user registration with:
     - Email validation
     - Password hashing
     - Database storage
     - JSON response

# The agent will create:
# - routes/auth.py with /register endpoint
# - models/user.py with user model
# - utils/security.py with password hashing
# - Update main.py
```

### Data Analysis

```bash
cd data-analysis
daveagent

You: read sales_2024.csv and create a summary report in JSON format

# The agent:
# 1. Reads sales_2024.csv
# 2. Calculates statistics (total, average, etc.)
# 3. Creates sales_summary.json with report
```

### Refactoring

```bash
cd legacy-code
daveagent

You: /search where is the database connection used

# CodeSearcher shows all files

You: refactor all database connections to use a connection pool

# The agent:
# 1. Creates db_pool.py with pool
# 2. Updates all files using the connection
# 3. Shows summary of changes
```

### Debugging

```bash
cd buggy-app
daveagent

You: @app.py there's a TypeError on line 45, fix it

# The agent:
# 1. Reads app.py line 45
# 2. Identifies the TypeError
# 3. Applies the fix
# 4. Explains what caused the error
```

---

## 🔍 Advanced Features (First Steps)

### 1. File Mentions with @

Mention specific files for maximum priority:

```bash
You: @auth.py @middleware.py update the authentication system to use JWT

# The agent:
# - auth.py has maximum priority
# - middleware.py also prioritized
# - Modifies both files in a coordinated way
```

**Navigation**:
- Type `@` and a file selector will appear
- Use ↑↓ to navigate
- Type to filter
- Enter to select

### 2. Memory System

```bash
# Index your project (do once)
You: /index
📚 Indexing project in vector memory...
✅ Indexing completed! 
  • Indexed files: 45
  • Chunks created: 234

# Now the agent can search semantically
You: where did we implement the caching logic?

# The agent searches vector memory and finds:
# - cache.py:12-45 - Redis caching implementation
# - models.py:67 - Model-level caching
```

### 3. Memory Between Sessions

```bash
# First session
You: my name is John and I prefer using async/await

# The agent saves: name=John, preference=async/await

# Second session (another day)
You: refactor this function

# The agent automatically uses async/await
# because it remembers your preference
```

---

## ⚙️ Quick Configuration

### Change AI Model

Edit `.env` in the project directory:

```env
DAVEAGENT_API_KEY=your-api-key
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_BASE_URL=https://api.openai.com/v1
```

### Disable SSL (Corporate Networks)

```bash
# Option 1: Argument
daveagent --no-ssl-verify

# Option 2: Environment variable
export DAVEAGENT_SSL_VERIFY=false
daveagent
```

---

## 🐛 Common Problems

### "Command not found: daveagent"

```bash
# Solution: Reinstall
cd DaveAgent
pip install -e .
```

### "SSL Certificate Error"

```bash
# Solution: Disable SSL verification
daveagent --no-ssl-verify
```

### "Connection Refused"

```bash
# Verify API key and base URL
cat .env

# Test connectivity
curl https://api.deepseek.com/v1
```

---

## ✅ Startup Checklist

- [ ] CodeAgent installed (`daveagent --version` works)
- [ ] API key configured (`.env` file)
- [ ] Project indexed (`/index` executed)
- [ ] Tested basic command (`read README.md`)
- [ ] Tested search (`/search main`)
- [ ] Tested file mention (`@README.md explain`)

---

## 🎓 Next Steps

Now that you know the basics:

1. **[Complete Usage Guide](Usage-Guide)** - Learn all commands and workflows
2. **[Tools](Tools-and-Features)** - Explore the 45+ available tools
3. **[Memory System](Memory-System)** - Master RAG memory
4. **[CodeSearcher](CodeSearcher)** - Advanced code search
5. **[File Mentions](File-Mentions)** - Interactive file selector

---

## 📞 Need Help?

- **Discord**: [Join our server](https://discord.gg/2dRTd4Cv) - Fastest way to get help
- **GitHub Issues**: [Report problems](https://github.com/davidmonterocrespo24/DaveAgent/issues)
- **Email**: contact@daveagent.ai

---

## 💡 Final Tips

1. **Use `/search` before modifying** - Understand code first
2. **Mention files with @** - Maximum priority for context
3. **Index your project** - `/index` for fast semantic searches
4. **Be specific** - Clear instructions = better results
5. **Use `/help`** - When you forget a command

---

Congratulations! 🎉 You now know how to use CodeAgent. Start coding with AI!

[← Back to Home](Home) | [Complete Guide →](Usage-Guide)
