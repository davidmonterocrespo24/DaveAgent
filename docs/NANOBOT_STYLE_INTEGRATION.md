# Nanobot-Style Subagent Integration

## Overview

CodeAgent now implements Nanobot-style subagent result injection, where background task results are naturally integrated into the main agent's conversation flow.

## Key Features

### 1. Subagent-Specific System Prompt

Subagents receive a focused system prompt that clearly defines their role and constraints:

- **Focused task assignment**: The exact task is embedded in the prompt
- **Clear capabilities**: What tools they can use
- **Clear restrictions**: Cannot spawn more subagents, access parent history, etc.
- **Output format**: Structured result format for consistency

**Location**: [src/config/prompts.py:500-570](src/config/prompts.py#L500-L570)

### 2. Result Injection System

When subagents complete, their results are queued as "announcements" that the main agent can retrieve:

```python
# Callback queues announcement
async def _on_subagent_completed(self, event):
    announce_content = f"""[Background Task Completed: '{label}']

Task: {task}

Result:
{result}

---
Please summarize this result naturally for the user in 1-2 sentences."""

    self._subagent_announcements.append({
        'label': label,
        'task': task,
        'result': result,
        'announcement': announce_content
    })
```

**Location**: [src/config/orchestrator.py:690-750](src/config/orchestrator.py#L690-L750)

### 3. Check Results Tool

The main agent uses `check_subagent_results()` to retrieve pending announcements:

```python
# Main agent calls this periodically
result = await check_subagent_results()

# Returns formatted announcement like:
"""
[Background Task Completed: 'file-analyzer']

Task: Analyze all Python files in src/

Result:
Found 42 Python files with a total of 5,230 lines...

---
Please summarize this result naturally for the user.
"""
```

**Location**: [src/tools/check_subagent_results.py](src/tools/check_subagent_results.py)

## Workflow Comparison

### Nanobot Flow

```
1. User: "Analyze file1 and file2"
2. Agent spawns 2 subagents
3. Subagents run in background
4. [MessageBus injects result as system message]
5. Main agent sees message naturally
6. Agent responds: "File1 has been analyzed..."
```

### CodeAgent Flow (Now)

```
1. User: "Analyze file1 and file2"
2. Agent spawns 2 subagents
3. Subagents run in background
4. Results queued in _subagent_announcements
5. Agent calls check_subagent_results()
6. Agent sees announcement and responds naturally
```

## Key Differences from Nanobot

| Aspect | Nanobot | CodeAgent |
|--------|---------|-----------|
| **Notification** | InboundMessage via MessageBus | Event queue + tool retrieval |
| **Result format** | Injected as user message | Retrieved via tool call |
| **Multi-platform** | Yes (Telegram, Discord, CLI) | CLI only |
| **Subagent loop** | Custom lightweight loop | Full AgentOrchestrator instance |
| **Automatic summarization** | Yes (via message injection) | Manual (via tool call) |

## Usage Example

### For Users

```bash
# Start CodeAgent
python src/main.py

# In conversation
You: "Analyze file1.py and file2.py in parallel"

Agent: "I'll spawn two subagents to analyze these files..."
       [Spawns 2 background tasks]

Agent: [Calls check_subagent_results periodically]

Agent: "File1 has been analyzed and contains 150 lines with 8 functions.
       File2 contains 200 lines with 12 functions."
```

### For Developers

```python
from src.config.orchestrator import AgentOrchestrator
from src.tools import spawn_subagent, check_subagent_results

# Initialize orchestrator
orch = AgentOrchestrator(...)

# Spawn subagent
await spawn_subagent(
    task="Analyze all Python files in src/",
    label="code-analyzer"
)

# Later, check for results
result = await check_subagent_results()
# Returns announcement with task, result, and request to summarize
```

## Implementation Details

### Initialization Sequence

1. **SubagentEventBus** created ([orchestrator.py:334](src/config/orchestrator.py#L334))
2. **SubAgentManager** created with factory ([orchestrator.py:335-339](src/config/orchestrator.py#L335-L339))
3. **spawn_subagent** tool initialized ([orchestrator.py:341-347](src/config/orchestrator.py#L341-L347))
4. **Announcement queue** created ([orchestrator.py:350](src/config/orchestrator.py#L350))
5. **check_subagent_results** tool initialized ([orchestrator.py:352-356](src/config/orchestrator.py#L352-L356))
6. **Event callbacks** subscribed ([orchestrator.py:359-360](src/config/orchestrator.py#L359-L360))

### Factory Pattern

Each subagent gets an isolated orchestrator instance:

```python
def _create_subagent_orchestrator(self, tools, max_iterations, mode, task):
    # Create new orchestrator
    subagent_orch = AgentOrchestrator(
        api_key=self.settings.api_key,
        # ... other settings ...
        headless=True,  # No UI
    )

    # Mark as subagent
    subagent_orch._is_subagent = True

    # Override with subagent-specific prompt
    if task:
        subagent_prompt = SUBAGENT_SYSTEM_PROMPT(task, workspace)
        subagent_orch.coder_agent.system_messages[0] = subagent_prompt

    return subagent_orch
```

**Location**: [src/config/orchestrator.py:596-650](src/config/orchestrator.py#L596-L650)

## Benefits

### Compared to Basic Event System

- ✅ Natural conversation flow (results become part of agent context)
- ✅ Agent decides when to check (not interrupt-driven)
- ✅ Clear instruction to summarize for user
- ✅ Batching possible (multiple results in one check)

### Compared to Direct Nanobot Approach

- ✅ No MessageBus dependency (simpler)
- ✅ Explicit tool call (more transparent)
- ✅ Works with existing AutoGen architecture
- ✅ Easy to test and debug

## Testing

Run the comprehensive test:

```bash
python test_nanobot_style.py
```

This will:
1. Initialize the orchestrator
2. Verify subagent system and tools
3. Spawn a test subagent
4. Wait for completion
5. Check announcements
6. Verify queue is cleared

## Future Enhancements

### Possible Improvements

1. **Auto-polling**: Have main agent automatically check results periodically
2. **Smart summarization**: Use LLM to automatically generate user-friendly summaries
3. **Priority queue**: Handle urgent results first
4. **Result expiration**: Clear old announcements after timeout
5. **Multi-platform**: Extend to Telegram/Discord like Nanobot

### Maintaining Nanobot Parity

Current gap: Nanobot injects results automatically, CodeAgent requires tool call.

**Option A**: Inject check call into agent loop automatically
**Option B**: Use system message injection (requires more AutoGen integration)
**Option C**: Current approach (explicit tool call) - simpler and more transparent

## Configuration

No configuration needed - the system is automatically initialized when you create an `AgentOrchestrator` instance.

The announcement queue and callbacks are set up during initialization and work transparently.

## Troubleshooting

### Announcements not appearing

1. Check subagent actually completed:
   ```bash
   /subagents  # List active subagents
   ```

2. Check for errors in logs:
   ```python
   orch.logger.handlers[0].stream  # View recent logs
   ```

3. Verify tool is registered:
   ```python
   tool_names = [t.__name__ for t in orch.all_tools["read_only"]]
   print("check_subagent_results" in tool_names)
   ```

### Subagent not using custom prompt

Verify factory is passing task:
```python
# In SubAgentManager._run_subagent
orchestrator = self.orchestrator_factory(
    tools=isolated_tools,
    max_iterations=max_iterations,
    mode="subagent",
    task=task,  # Must be passed!
)
```

### Tool not found

Ensure imports in [src/tools/__init__.py](src/tools/__init__.py):
```python
from src.tools.check_subagent_results import check_subagent_results

__all__ = [
    # ...
    "check_subagent_results",
]
```

## References

- **Nanobot source**: [nanobot/agent/subagent.py](../nanobot/nanobot/agent/subagent.py)
- **Comparison doc**: [COMPARACION_NANOBOT.md](../COMPARACION_NANOBOT.md)
- **Subagent docs**: [docs/skills/subagents.md](skills/subagents.md)
- **Test suite**: [test_nanobot_style.py](../test_nanobot_style.py)
