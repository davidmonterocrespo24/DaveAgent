# 🛠️ Tools and Features - CodeAgent

CodeAgent includes **45+ integrated tools**, organized in 6 main categories. This page documents each tool with usage examples.

## 📊 Tools Summary

| Category | Quantity | Description |
|----------|----------|-------------|
| [📁 Filesystem](#-filesystem-7-tools) | 7 | File and directory operations |
| [🔀 Git](#-git-8-tools) | 8 | Complete version control |
| [📊 JSON](#-json-8-tools) | 8 | JSON processing and validation |
| [📈 CSV](#-csv-7-tools) | 7 | CSV analysis and manipulation |
| [🌐 Web](#-web-7-tools) | 7 | Wikipedia and web search |
| [🔍 Analysis](#-analysis-5-tools) | 5 | Python code analysis and search |
| [🧠 Memory](#-memory-8-tools) | 8 | RAG vector memory system |

**Total**: **50 tools**

---

## 📁 Filesystem (7 tools)

### `read_file`
Reads file content with support for line ranges.

**Examples**:
```bash
You: read the README.md file
You: read main.py lines 10 to 50
You: show me the content of config.py
```

### `write_file`
Creates or overwrites a file with content.

**Examples**:
```bash
You: create a file utils.py with a function to validate emails
You: write a new config.json with the database settings
```

### `edit_file`
Edits files using surgical search and replace.

**Examples**:
```bash
You: @auth.py change the password hash algorithm to bcrypt
You: in config.py, update the database URL
You: fix the typo in line 45 of main.py
```

### `list_dir`
Lists directory contents.

**Examples**:
```bash
You: list files in the src/ directory
You: show me what's in the current directory
You: list all files in utils/
```

### `delete_file`
Safely deletes a file.

**Examples**:
```bash
You: delete the old_config.py file
You: remove test_old.py
```

### `file_search`
Fuzzy file search by name.

**Examples**:
```bash
You: find files with 'auth' in the name
You: search for config files
```

### `glob_search`
File search using glob patterns.

**Examples**:
```bash
You: find all Python files (*.py)
You: search for all JSON files in src/
You: list all test files (**/*test*.py)
```

---

## 🔀 Git (8 tools)

### `git_status`
Gets Git repository status.

**Examples**:
```bash
You: show git status
You: what files have changed?
```

### `git_add`
Adds files to staging area.

**Examples**:
```bash
You: git add main.py
You: stage all changes
You: add all Python files
```

### `git_commit`
Creates a commit with staged changes.

**Examples**:
```bash
You: commit with message "Added authentication"
You: create a commit for these changes
```

### `git_push`
Pushes commits to remote repository.

**Examples**:
```bash
You: push changes to origin
You: git push to main branch
```

### `git_pull`
Gets changes from remote repository.

**Examples**:
```bash
You: pull latest changes
You: git pull from origin
```

### `git_log`
Shows commit history.

**Examples**:
```bash
You: show last 5 commits
You: git log with 10 entries
```

### `git_branch`
Manages branches: list, create, delete, switch.

**Examples**:
```bash
You: list all branches
You: create a new branch feature/auth
You: switch to main branch
You: delete branch old-feature
```

### `git_diff`
Shows repository differences.

**Examples**:
```bash
You: show git diff
You: what changed in staged files?
You: diff of working tree
```

---

## 📊 JSON (8 tools)

### `read_json`
Reads and parses a JSON file.

**Examples**:
```bash
You: read the package.json file
You: show me the content of config.json
```

### `write_json`
Writes data to a JSON file.

**Examples**:
```bash
You: create a config.json with database settings
You: write user data to users.json
```

### `merge_json_files`
Combines two JSON files into one.

**Examples**:
```bash
You: merge config1.json and config2.json into final_config.json
You: combine user data from two JSON files
```

### `validate_json`
Validates that a file contains valid JSON.

**Examples**:
```bash
You: validate the syntax of config.json
You: check if data.json is valid JSON
```

### `format_json`
Formats a JSON file with consistent indentation.

**Examples**:
```bash
You: format config.json with proper indentation
You: prettify the messy JSON file
```

### `json_get_value`
Gets a specific value using key path (dot notation).

**Examples**:
```bash
You: get the value of user.name from config.json
You: extract database.host from settings.json
```

### `json_set_value`
Sets a specific value using key path.

**Examples**:
```bash
You: set user.email to "test@example.com" in config.json
You: update database.port to 5432 in settings.json
```

### `json_to_text`
Converts a JSON file to readable text format.

**Examples**:
```bash
You: convert config.json to readable text
You: show data.json in text format
```

---

## 📈 CSV (7 tools)

### `read_csv`
Reads a CSV file and shows its content.

**Examples**:
```bash
You: read the sales.csv file
You: show me the first 10 rows of data.csv
You: read customers.csv with semicolon delimiter
```

### `write_csv`
Writes data to a CSV file.

**Examples**:
```bash
You: create a products.csv with columns: id, name, price
You: write sales data to output.csv
```

### `csv_info`
Gets statistical information about a CSV file.

**Examples**:
```bash
You: show statistics for sales.csv
You: get column types and null values from data.csv
You: analyze the structure of customers.csv
```

### `filter_csv`
Filters a CSV by column value.

**Examples**:
```bash
You: filter sales.csv where product="Laptop"
You: get all rows from customers.csv where country="USA"
You: find sales in data.csv where amount > 1000
```

### `merge_csv_files`
Combines two CSV files.

**Examples**:
```bash
You: merge sales_2023.csv and sales_2024.csv
You: join customers.csv and orders.csv on customer_id
You: concatenate all monthly reports
```

### `csv_to_json`
Converts a CSV file to JSON format.

**Examples**:
```bash
You: convert sales.csv to sales.json
You: transform data.csv to JSON format
```

### `sort_csv`
Sorts a CSV by column.

**Examples**:
```bash
You: sort sales.csv by amount in descending order
You: order customers.csv by name alphabetically
```

---

## 🌐 Web (7 tools)

### `wiki_search`
Searches for Wikipedia articles related to a query.

**Examples**:
```bash
You: search Wikipedia for "Python programming"
You: find articles about "machine learning"
```

### `wiki_summary`
Gets a summary of a Wikipedia article.

**Examples**:
```bash
You: get a summary of the Python article on Wikipedia
You: show me a brief description of "FastAPI"
```

### `wiki_content`
Gets the complete content of an article.

**Examples**:
```bash
You: get the full content of "Git" article
You: show me the complete Wikipedia page for "REST API"
```

### `wiki_page_info`
Gets detailed information about a Wikipedia page.

**Examples**:
```bash
You: get metadata for "Python programming" page
You: show categories and links for "Docker" article
```

### `wiki_random`
Gets random Wikipedia page titles.

**Examples**:
```bash
You: get 5 random Wikipedia pages
You: show me a random article
```

### `wiki_set_language`
Changes language for Wikipedia searches.

**Examples**:
```bash
You: set Wikipedia language to Spanish
You: change wiki language to French (fr)
```

### `web_search`
General web search.

**Examples**:
```bash
You: search the web for "best Python frameworks 2024"
You: find information about "Docker deployment"
```

---

## 🔍 Analysis (5 tools)

### `analyze_python_file`
Analyzes a Python file to extract its structure.

**Examples**:
```bash
You: analyze the structure of main.py
You: show imports, classes, and functions in auth.py
```

**Output**:
```python
# Imports:
- import os
- from fastapi import FastAPI

# Classes:
- UserModel (lines 10-25)
- AuthService (lines 30-50)

# Functions:
- validate_user(email, password) (lines 55-70)
- create_token(user_id) (lines 75-85)
```

### `find_function_definition`
Finds and shows a specific function definition.

**Examples**:
```bash
You: find the definition of login_user in auth.py
You: show me the validate_email function
```

### `list_all_functions`
Lists all functions in a Python file.

**Examples**:
```bash
You: list all functions in utils.py
You: show me all methods in the services.py file
```

### `grep_search`
Text search with patterns (regex).

**Examples**:
```bash
You: search for "def authenticate" in all Python files
You: find where "database_url" is used
You: grep for "TODO" comments in src/
```

### `run_terminal_cmd`
Executes shell commands.

**Examples**:
```bash
You: run pytest to test the application
You: execute npm install
You: run the Flask development server
```

---

## 🧠 Memory (8 tools)

RAG (Retrieval-Augmented Generation) system with ChromaDB for persistent memory.

### Query Tools

#### `query_conversation_memory`
Searches in past conversation history.

**Examples**:
```bash
You: what did we discuss about authentication last week?
You: find conversations about database optimization
```

#### `query_codebase_memory`
Searches in indexed project code.

**Examples**:
```bash
You: where did we implement caching logic?
You: find the authentication middleware code
```

#### `query_decision_memory`
Searches recorded architectural decisions.

**Examples**:
```bash
You: what was our decision about the database schema?
You: recall our choice for the API framework
```

#### `query_preferences_memory`
Searches user preferences.

**Examples**:
```bash
You: what's my preferred coding style?
You: recall my framework preferences
```

#### `query_user_memory`
Searches user information.

**Examples**:
```bash
You: what's my name and role?
You: recall my expertise areas
```

### Save Tools

#### `save_user_info`
Saves information about the user.

**Examples**:
```bash
You: remember that my name is John and I'm a backend developer
You: save that I work on microservices architecture
```

#### `save_decision`
Records an architectural decision.

**Examples**:
```bash
You: remember we decided to use PostgreSQL for the database
You: save our decision to implement JWT authentication
```

#### `save_preference`
Saves a user preference.

**Examples**:
```bash
You: remember I prefer async/await over callbacks
You: save that I like using FastAPI over Flask
```

---

## 📎 Special Features

### File Mentions with @

Mention specific files to give them maximum priority in context.

**Syntax**: `@<filename>`

**Features**:
- Interactive selector with keyboard navigation (↑↓)
- Real-time search and filtering
- Mentioned files have **maximum priority**
- Supports multiple files in a single query
- Automatically excludes hidden and binary files

**Examples**:
```bash
You: @main.py explain how this file works
You: @config.py @.env update the database settings
You: @auth.py add docstrings to all functions
You: @src/agents/coder.py refactor to use async
```

**More info**: See [File Mentions Guide](File-Mentions)

### /search Command (CodeSearcher)

The `/search` command invokes the specialized **CodeSearcher** agent.

**Usage**:
```bash
You: /search authentication function
You: /search where is TaskPlanner used
You: /search how does logging work
```

**CodeSearcher provides**:
- 📍 Relevant files with exact locations
- 🔧 Found functions with complete code
- 📦 Important variables and constants
- 🔗 Dependencies between components
- 💡 Recommendations on what to modify

**More info**: See [CodeSearcher Guide](CodeSearcher)

### /index Command (Project Indexing)

Indexes your project in vector memory for fast semantic searches.

**Usage**:
```bash
You: /index

# Output:
📚 Indexing project in vector memory...
✅ Indexing completed!
  • Indexed files: 45
  • Chunks created: 234
```

**Benefits**:
- Instant semantic search
- Agent remembers project structure
- Faster and more accurate queries

**More info**: See [Memory System](Memory-System)

---

## 🎯 How to Use Tools

### Natural Way (Recommended)

Simply describe what you need in natural language:

```bash
You: read the README.md file
You: create a new utils.py with email validation
You: show me the git status
You: search for "login" function in the codebase
```

The agent automatically selects the appropriate tools.

### Direct Way (For advanced users)

You can also be more specific:

```bash
You: use read_file to show main.py lines 10-50
You: run git_status to check repository state
You: use analyze_python_file on auth.py
```

---

## 💡 Usage Tips

1. **Combine tools**: The agent can use multiple tools in one task
   ```bash
   You: read auth.py, find the login function, and add error handling
   # Uses: read_file + find_function_definition + edit_file
   ```

2. **Use /search before modifying**: Understand the code first
   ```bash
   You: /search authentication system
   # Then: modify the auth logic
   ```

3. **Leverage memory**: The agent remembers between sessions
   ```bash
   # Session 1
   You: /index
   
   # Session 2 (another day)
   You: where did we put the caching logic?
   ``` 

4. **File mentions for precision**: Use @ when you know which file you need
   ```bash
   You: @config.py update database URL to localhost
   ```

---

## 📚 See Also

- **[CodeSearcher](CodeSearcher)** - Specialized search agent
- **[File Mentions](File-Mentions)** - Complete file mentions guide
- **[Memory System](Memory-System)** - RAG memory system
- **[Usage Guide](Usage-Guide)** - Complete usage guide
- **[Configuration](Configuration)** - Tools configuration

---

[← Back to Home](Home) | [Architecture →](Architecture)
