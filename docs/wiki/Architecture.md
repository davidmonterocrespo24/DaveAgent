#  CodeAgent Architecture

This page describes the technical architecture of CodeAgent, its main components, and how they interact with each other.

##  Overview

CodeAgent follows a modular architecture based on specialized agents, where each component has clearly defined responsibilities.

```

                    User (CLI)                            

                     

              CLI Interface (Rich)                        
           prompt-toolkit + Rich formatting               

                     

           Conversation Manager                           
  - History management                                   
  - Automatic compression                                
  - Token estimation                                     

                     
       
                                   
          
 Complexity                Memory        
  Detector                 System        
            (ChromaDB)     
                         
       

            Agent Router                                
  Determines: SIMPLE vs COMPLEX workflow                

       
        SIMPLE 
                     
             
                Direct Execution        
                - Coder Agent           
                - Code Searcher         
             
       
        COMPLEX 
                      
              
                Planning Workflow        
                 
                 Planning Agent       
                 
                                        
                 
                 SelectorGroupChat    
                  - CodeSearcher      
                  - Coder             
                  - Summary           
                 
              
                      
              
                   Tools (45+)          
                - Filesystem (7)        
                - Git (8)               
                - Data (15)             
                - Web (7)               
                - Analysis (5)          
                - Memory (8)            
              
```

---

##  Project Structure

```
CodeAgent/
 src/                          # Main source code
    __init__.py
   
    agents/                   #  System agents
       __init__.py
       task_planner.py       # Task planner
       task_executor.py      # Task executor
       code_searcher.py      # Code searcher
   
    managers/                 #  System managers
       __init__.py
       conversation_manager.py  # Conversation management
   
    interfaces/               #  User interfaces
       __init__.py
       cli_interface.py      # CLI interface with Rich
   
    config/                   #  Configuration
       __init__.py
       prompts.py            # System prompts
   
    memory/                   #  Memory system
       __init__.py
       memory_manager.py     # RAG memory manager
       chroma_manager.py     # ChromaDB interface
       embeddings.py         # Embedding generation
   
    observability/            #  Observability
       __init__.py
       langfuse_tracer.py    # Langfuse tracing
   
    utils/                    #  Utilities
       __init__.py
       logger.py             # Logging system
       file_utils.py         # File utilities
       token_counter.py      # Token counting
   
    tools/                    #  Tools (45+)
       __init__.py           # Exports all tools
       read_file.py          # File reading
       write_file.py         # File writing
       edit_file.py          # File editing
       delete_file.py        # File deletion
       directory_ops.py      # Directory operations
       search_file.py        # File search
       glob.py               # Glob pattern search
       git_operations.py     # Git operations (8 tools)
       json_tools.py         # JSON tools (8)
       csv_tools.py          # CSV tools (7)
       wikipedia_tools.py    # Wikipedia tools
       web_search.py         # Web search
       code_analyzer.py      # Python code analysis
       grep.py               # Text pattern search
       terminal.py           # Command execution
       memory_tools.py       # RAG memory tools (8)
       common.py             # Common utilities
   
    cli.py                    # CLI entry point
    main.py                   # Main application

 eval/                         #  SWE-bench evaluation
    agent_wrapper.py          # Agent wrapper
    run_inference.py          # Inference execution
    README.md                 # Evaluation documentation

 docs/                         #  Documentation
    STRUCTURE.md              # Project structure
    MEMORY_SYSTEM.md          # Memory system
    CODESEARCHER_GUIDE.md     # CodeSearcher guide
    ...                       # Other documents

 test/                         #  Tests
    test_tools.py
    test_agents.py
    ...

 .daveagent/                   # Local configuration
    .env                      # Environment variables
    memory/                   # ChromaDB database

 logs/                         #  Execution logs

 requirements.txt              # Dependencies
 pyproject.toml                # Project configuration
 setup.py                      # Installation script
 README.md                     # Main documentation
```

---##  Main Components

### 1. **CLI Interface** (`src/interfaces/cli_interface.py`)

**Responsibilities**:
- Interactive user interface using `prompt-toolkit`
- Rich formatting with `rich` (colors, tables, panels)
- Command and file autocompletion
- Special command handling (`/help`, `/search`, etc.)

**Technologies**:
- `prompt-toolkit`: Autocompletion and navigation
- `rich`: Output formatting and colors

### 2. **Conversation Manager** (`src/managers/conversation_manager.py`)

**Responsibilities**:
- Conversation history management
- Token usage estimation
- Automatic compression when history grows
- Maintains relevant context for agents

**Features**:
```python
- max_tokens: 8000 (maximum limit)
- summary_threshold: 6000 (compression threshold)
- Algorithm: Keeps last 3 messages + summary
```

### 3. **Complexity Detector**

**Responsibilities**:
- Analyzes user request
- Determines if it requires SIMPLE or COMPLEX workflow
- Uses LLM for intelligent classification

**Criteria**:
```python
SIMPLE:
  - 1-5 files
  - Direct modifications
  - Code searches
  - Git operations

COMPLEX:
  - 6+ files
  - Complete systems
  - Requires planning
  - Multi-component architecture
```

### 4. **Specialized Agents** (`src/agents/`)

#### A) **PlanningAgent** (COMPLEX only)
- Creates structured execution plans
- Tracks task progress
- Re-plans dynamically if necessary
- NO tools, only plans

#### B) **CodeSearcher** (Both workflows)
- Code search and analysis
- Does NOT modify code
- Uses: `grep_search`, `read_file`, `analyze_python_file`
- Provides locations and references

#### C) **Coder** (Both workflows)
- Executes code modifications
- Has access to ALL 45+ tools
- Creates, edits, and deletes files
- Executes Git commands

#### D) **SummaryAgent** (Both workflows)
- Creates final summaries
- Lists created/modified files
- Identifies next steps
- Marks task as completed

### 5. **Memory System** (`src/memory/`)

**Architecture**:
```
Memory Manager
    
     ChromaDB (Vector database)
        conversations (history)
        codebase (indexed code)
        decisions (architectural decisions)
        preferences (user preferences)
        user_info (user information)
    
     Embeddings (BGE M3-Embedding)
        - Vector generation
        - Semantic search
```

**Memory Tools** (8):
- `query_conversation_memory`: Search past conversations
- `query_codebase_memory`: Search indexed code
- `query_decision_memory`: Recall decisions
- `query_preferences_memory`: User preferences
- `query_user_memory`: User information
- `save_user_info`: Save user info
- `save_decision`: Record decision
- `save_preference`: Save preference

### 6. **Tool System** (`src/tools/`)

**Organization by Category**:

| Category | Quantity | Location | Description |
|----------|----------|----------|-------------|
| **Filesystem** | 7 | `tools/read_file.py`, `write_file.py`, `edit_file.py`, `delete_file.py`, `directory_ops.py`, `search_file.py`, `glob.py` | File operations |
| **Git** | 8 | `tools/git_operations.py` | Version control |
| **JSON** | 8 | `tools/json_tools.py` | JSON processing |
| **CSV** | 7 | `tools/csv_tools.py` | CSV analysis |
| **Web** | 7 | `tools/wikipedia_tools.py`, `web_search.py` | Wikipedia, web search |
| **Analysis** | 5 | `tools/code_analyzer.py`, `grep.py`, `terminal.py` | Code analysis |
| **Memory** | 8 | `tools/memory_tools.py` | RAG and persistence |

### 7. **Observability** (`src/observability/`)

**Langfuse Integration**:
- LLM call tracing
- Performance metrics
- Cost analysis
- Agent debugging

---

##  Workflows

### SIMPLE Workflow (Direct Tasks)

```
User → CLI Interface → Conversation Manager
    ↓
Complexity Detector (→ SIMPLE)
    ↓
Selector: CodeSearcher or Coder
    ↓
 CodeSearcher (if search needed)
    Analysis and references
 Coder (direct execution)
     Tools (read_file, write_file, git, etc.)
    ↓
Summary Agent
     Final summary
```

**Example**:
```
User: "Fix the bug in auth.py line 45"
  → Coder reads auth.py
  → Coder applies edit_file
  → Summary shows changes
```

### COMPLEX Workflow (Multi-step Projects)

```
User → CLI Interface → Conversation Manager
    ↓
Complexity Detector (→ COMPLEX)
    ↓
Planning Agent
    ↓
Creates Plan:
  1. [ ] Search existing structure
  2. [ ] Create models
  3. [ ] Implement endpoints
  4. [ ] Add tests
    ↓
SelectorGroupChat
     Task 1 → CodeSearcher (searches structure)
                Planning Agent updates plan
     Task 2 → Coder (creates models)
                Planning Agent updates plan
     Task 3 → Coder (implements endpoints)
                Planning Agent updates plan
     Task 4 → Coder (adds tests)
                 Planning Agent → DELEGATE_TO_SUMMARY
    ↓
Summary Agent
     Complete project summary
```

**Example**:
```
User: "Create a REST API with FastAPI for user management"
  → Planning Agent: Creates 6-step plan
  → Step 1: CodeSearcher reviews project
  → Step 2: Coder creates models/user.py
  → Step 3: Coder creates routes/users.py
  → Step 4: Coder creates schemas/user.py
  → Step 5: Coder adds tests
  → Step 6: Coder updates main.py
  → Summary: Lists all created files
```

---

##  Prompt System

All prompts are centralized in `src/config/prompts.py`:

| Prompt | Agent | Purpose |
|--------|-------|---------|
| `AGENT_SYSTEM_PROMPT` | Coder | Code modification instructions |
| `CODE_SEARCHER_SYSTEM_MESSAGE` | CodeSearcher | Search and analysis only |
| `PLANNING_AGENT_SYSTEM_MESSAGE` | Planning | Plan creation and management |
| `SUMMARY_AGENT_SYSTEM_MESSAGE` | Summary | Final summaries |
| `COMPLEXITY_DETECTOR_PROMPT` | Classifier | SIMPLE vs COMPLEX detection |

---

##  State Management

### Conversation History

```python
message = {
    "role": "user" | "assistant" | "system",
    "content": "...",
    "timestamp": datetime,
    "metadata": {
        "tokens": int,
        "agent": str,
        "tool_calls": [...]
    }
}
```

### Automatic Compression

When `len(messages) * avg_tokens > summary_threshold`:
1. Creates summary prompt
2. Summarizer Agent generates concise summary
3. Keeps last 3 messages + summary
4. Significantly reduces token usage

---

##  AutoGen 0.4 Integration

CodeAgent uses AutoGen 0.4 with the following features:

- **AssistantAgent**: Agents with tools
- **SelectorGroupChat**: Multiple agent orchestration
- **FunctionSchema**: Tool definition
- **OpenAIChatCompletionClient**: Compatible LLM client

---

##  Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Scalability**: Easy to add new tools and agents
3. **Simplicity**: SIMPLE workflow for everyday tasks
4. **Planning**: COMPLEX workflow for large projects
5. **Persistent Memory**: ChromaDB for cross-session context
6. **Observability**: Langfuse for tracing and metrics

---

##  Technologies Used

| Technology | Version | Purpose |
|------------|---------|---------|
| **AutoGen** | >=0.4.0 | Agent framework |
| **ChromaDB** | >=0.4.0 | Vector database |
| **Rich** | >=13.0.0 | Terminal formatting |
| **Prompt Toolkit** | >=3.0.0 | Interactive CLI |
| **Pandas** | >=2.0.0 | Data processing |
| **Langfuse** | >=2.0.0 | Observability |
| **Python** | >=3.10 | Base language |

---

##  See Also

- **[Tools and Features](Tools-and-Features)** - Complete tool catalog
- **[Memory System](Memory-System)** - RAG system details
- **[Development](Development)** - How to contribute
- **[SWE-bench Evaluation](SWE-Bench-Evaluation)** - Agent benchmarking

---

[← Back to Home](Home) | [Tools →](Tools-and-Features)
