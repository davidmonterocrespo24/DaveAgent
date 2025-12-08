# DaveAgent CLI - Interactive Interface

Intelligent development agent with dynamic task planning and automatic conversation history management.

## Features

✨ **Intelligent Planning**: Automatically creates an execution plan with specific tasks
🔄 **Dynamic Re-planning**: Adapts the plan if errors or new information are found
💾 **History Management**: Automatic compression when history grows
🎨 **Rich Interface**: Interactive CLI with colors and enriched formatting
🛠️ **Integrated Tools**: File reading/writing, search, command execution

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Start the agent

```bash
python main.py
```

### Available commands

- `/help` - Show help
- `/new` - Start a new conversation without history (clears all context)
- `/clear` - Clear conversation history
- `/plan` - Show current execution plan
- `/stats` - Show session statistics
- `/save <file>` - Save history to a file
- `/load <file>` - Load history from a file
- `/exit` or `/quit` - Exit the agent

### Usage examples

**Example 1: Create an API**
```
You: Create a REST API with FastAPI that has endpoints to manage users (full CRUD)
```

The agent will:
1. Create a plan with tasks such as:
   - Check if FastAPI exists in the project
   - Create directory structure
   - Create data models
   - Implement CRUD endpoints
   - Create main.py file
   - Add documentation

2. Show you the plan and ask for confirmation

3. Execute each task sequentially

4. If it encounters errors, it will automatically re-plan


**Example 2: Refactor code**
```
You: Find all Python files that use callbacks and refactor them to use async/await
```

**Example 3: Bug fixing**
```
You: Find and fix all type errors in the project
```

### Example 4: Start new conversation

```
You: /new

[The agent clears all history and current plan]
[You can start with a completely new task without previous context]

You: Now help me create an authentication system with JWT
```

The `/new` command is useful when:

- You want to completely change tasks
- The history has become very long and you prefer to start from scratch
- You need the agent to "forget" the previous context
- You want to make sure there's no interference from previous tasks

## Architecture

### Main Components

#### 1. ConversationManager (`conversation_manager.py`)
Manages conversation history with automatic compression:
- Estimates tokens used
- Creates summaries when history grows
- Maintains relevant context for the agent

#### 2. TaskPlanner (`task_planner.py`)
Planning system with two specialized agents:
- **Planner Agent**: Creates structured execution plans
- **PlanUpdater Agent**: Adapts plans based on results
- Manages dependencies between tasks
- Updates states (pending, in_progress, completed, failed, blocked)

#### 3. TaskExecutor (`task_executor.py`)
Executor with dynamic re-planning:
- Executes plan tasks sequentially
- Detects when it needs to re-plan
- Compresses history automatically
- Handles errors and retries

#### 4. CLIInterface (`cli_interface.py`)
Rich and interactive CLI interface:
- Uses `rich` for enriched formatting
- Uses `prompt-toolkit` for autocompletion
- Shows real-time progress
- Visual formats for plans and results

### Workflow

```
User enters request
         ↓
ConversationManager saves to history
         ↓
TaskPlanner creates execution plan
         ↓
CLI shows plan and asks for confirmation
         ↓
TaskExecutor executes tasks
         ↓
For each task:
    ├─ Executes using CoderAgent
    ├─ Analyzes result
    ├─ Needs re-planning? → TaskPlanner updates plan
    └─ Continues with next task
         ↓
History too large? → ConversationManager compresses
         ↓
Plan completed → Shows summary
```

## File Structure

```
DaveAgent/
├── main.py                      # Main entry point
├── conversation_manager.py       # History management
├── task_planner.py              # Task planning
├── task_executor.py             # Task execution
├── cli_interface.py             # CLI interface
├── coder.py                     # Original code agent
├── tools.py                     # Agent tools
├── prompt.py                    # System prompts
├── requirements.txt             # Dependencies
└── README_CLI.md               # This documentation
```

## Configuration

### Change the model

Edit `main.py`:

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

### Adjust history limits

Edit `main.py`:

```python
self.conversation_manager = ConversationManager(
    max_tokens=8000,              # Maximum limit
    summary_threshold=6000        # Threshold to compress
)
```

## Advanced Features

### Planning with Dependencies

The system automatically handles dependencies between tasks:

```python
Task(
    id=2,
    title="Create models",
    dependencies=[1]  # Depends on task 1
)
```

### Intelligent Re-planning

The system automatically detects when to re-plan based on:
- Execution errors
- Unexpected results
- Keywords in results ("error", "missing", "necessary", etc.)

### History Compression

When history exceeds the threshold:
1. Creates a summary prompt
2. Uses a Summarizer agent to generate concise summary
3. Keeps only the last 3 messages + summary
4. Significantly reduces token usage

## Troubleshooting

### Error: "Could not generate plan"
- Verify that the model supports structured JSON
- Check API key and connectivity

### Error: "Iteration limit reached"
- The plan has circular dependencies
- Increase `max_iterations` in `task_executor.py`

### The agent does not respond
- Verify that all dependencies are installed
- Check error logs in the console

## Contributing

To add new tools to the agent:

1. Create the function in `tools.py`
2. Add it to `coder_tools` in `main.py`
3. The agent will detect it automatically

## License

This project is open source.
