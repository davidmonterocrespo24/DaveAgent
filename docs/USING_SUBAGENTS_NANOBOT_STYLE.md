# Using Subagents - Nanobot Style

## Quick Start

### Basic Usage

The agent can now spawn background tasks (subagents) and automatically retrieve their results for you.

```
You: "Analyze file1.py and file2.py - do them in parallel to save time"

Agent: "I'll spawn two subagents to analyze these files in parallel..."
       [Spawns subagent 'analyzer-1' for file1.py]
       [Spawns subagent 'analyzer-2' for file2.py]

       [Later, after checking results]
       "File1 contains 150 lines with 8 functions.
        File2 contains 200 lines with 12 functions."
```

### What Happens Behind the Scenes

1. **Agent spawns subagents** using `spawn_subagent` tool
2. **Subagents run in background** with their own isolated context
3. **Results are queued** when subagents complete
4. **Agent checks results** using `check_subagent_results` tool
5. **Agent summarizes** the results naturally for you

## When to Use Subagents

### Good Use Cases ✅

- **Parallel analysis**: Analyze multiple files simultaneously
- **Long-running tasks**: Background compilation, test runs, file searches
- **Independent tasks**: Tasks that don't depend on each other
- **Resource-intensive**: Tasks that might take time (web searches, etc.)

**Example requests**:
- "Analyze all Python files in src/ (do it in the background)"
- "Search for TODO comments in the codebase and also run the tests"
- "Fetch the latest docs from the website while I review the current code"

### Not Recommended ❌

- **Sequential dependencies**: Task B needs result from Task A
- **Quick operations**: Reading a single file (faster to do directly)
- **Interactive tasks**: Tasks needing user input
- **Single simple task**: No benefit to parallelism

## How the Agent Uses Subagents

### Spawning

The agent uses the `spawn_subagent` tool:

```python
await spawn_subagent(
    task="Analyze all Python files in src/ directory. Count total lines, functions, and classes.",
    label="code-analyzer"  # Human-readable label for tracking
)
# Returns: "Subagent 'code-analyzer' spawned (ID: abc12345)"
```

### Checking Results

The agent periodically checks for completed subagents:

```python
result = await check_subagent_results()
# Returns announcement with task details and results
```

The announcement format:
```
[Background Task Completed: 'code-analyzer']

Task: Analyze all Python files in src/ directory...

Result:
Found 42 Python files totaling 5,230 lines of code.
Breakdown:
- 850 lines in orchestrator.py
- 620 lines in agents.py
...

---
Please summarize this result naturally for the user in 1-2 sentences.
```

### Agent's Natural Summary

The agent then responds to you naturally:
```
"I've finished analyzing the codebase. There are 42 Python files with
5,230 lines total, with orchestrator.py being the largest at 850 lines."
```

## Monitoring Subagents

### CLI Commands

You can check on active subagents while the agent is working:

```bash
# List all active subagents
/subagents

# Check status of specific subagent
/subagent-status <id>
```

**Example output**:
```
Active Subagents
┌──────────┬──────────────┬──────────┐
│ ID       │ Status       │ Started  │
├──────────┼──────────────┼──────────┤
│ abc12345 │ running      │ 5s ago   │
└──────────┴──────────────┴──────────┘
```

## Subagent Capabilities

### What Subagents Can Do

- ✅ Read and write files
- ✅ Run terminal commands
- ✅ Search the web
- ✅ Use all standard tools
- ✅ Complete complex tasks independently

### What Subagents Cannot Do

- ❌ Spawn more subagents (prevents infinite recursion)
- ❌ Access parent conversation history
- ❌ Interact with user directly
- ❌ Change their assigned task

## Example Workflows

### Parallel File Analysis

**Your request**:
```
"I need to analyze file1.py, file2.py, and file3.py for code quality issues"
```

**Agent's approach**:
```
1. Spawns 3 subagents (one per file)
2. Each analyzes independently in parallel
3. Agent checks results as they complete
4. Agent combines findings into summary
5. You get comprehensive report
```

**Time saved**: 3x faster than sequential analysis!

### Background Research + Current Work

**Your request**:
```
"Look up the latest React documentation while I review the current implementation"
```

**Agent's approach**:
```
1. Spawn subagent to fetch React docs
2. Main agent reviews current code
3. When docs arrive, agent integrates information
4. You get analysis with latest best practices
```

**Benefit**: Parallel work, no waiting!

### Test Run + Code Analysis

**Your request**:
```
"Run the test suite and analyze the coverage report"
```

**Agent's approach**:
```
1. Spawn subagent to run tests (long-running)
2. Main agent continues to be responsive
3. When tests complete, agent analyzes results
4. You get test results + analysis
```

**Benefit**: Can interact during test run!

## Tips for Best Results

### Be Explicit About Parallelism

❌ "Analyze these files"
✅ "Analyze these files in parallel" or "Do this in the background"

The agent will better understand your intent.

### Provide Clear Task Descriptions

When the agent spawns subagents, clear tasks help:

✅ "Analyze file.py for security issues, focusing on SQL injection and XSS"
❌ "Check file.py"

### Check Status Anytime

Use `/subagents` command to see what's running:
```
You: /subagents

┌──────────┬───────────────┬──────────┐
│ ID       │ Status        │ Started  │
├──────────┼───────────────┼──────────┤
│ a1b2c3d4 │ running       │ 10s ago  │
│ e5f6g7h8 │ running       │ 8s ago   │
└──────────┴───────────────┴──────────┘
```

## Advanced: Understanding Subagent Isolation

Each subagent:
- Has its own isolated orchestrator instance
- Cannot see other subagents' work
- Has a focused system prompt for its specific task
- Runs with limited iterations (default: 15)
- Auto-cleans up when done

This ensures:
- ✅ No state conflicts
- ✅ Predictable behavior
- ✅ Resource efficiency
- ✅ Clean failure handling

## Troubleshooting

### "No pending subagent results"

This means either:
1. Subagents haven't completed yet (still running)
2. No subagents were spawned
3. Results were already retrieved

**Solution**: Use `/subagents` to check if tasks are still running.

### Subagent Fails

If a subagent fails, you'll get an announcement:
```
[Background Task Failed: 'analyzer-1']

Task: Analyze file1.py

Error: FileNotFoundError: file1.py not found

---
Please inform the user about this failure...
```

The agent will inform you and suggest alternatives.

### Too Many Subagents

While there's no hard limit, spawning too many subagents (>10) at once may:
- Use significant resources
- Make coordination complex
- Slow down overall performance

**Best practice**: Spawn 2-5 subagents for typical workflows.

## Comparison with Direct Execution

### Without Subagents (Sequential)

```
Task 1: 10 seconds
Task 2: 10 seconds
Task 3: 10 seconds
Total: 30 seconds
```

### With Subagents (Parallel)

```
Task 1: 10 seconds ┐
Task 2: 10 seconds ├─ All run simultaneously
Task 3: 10 seconds ┘
Total: ~10 seconds (+ small overhead)
```

**Speedup**: 3x faster for independent tasks!

## FAQ

**Q: Do I need to explicitly ask for subagents?**
A: No, the agent will use them when appropriate. But you can suggest it for clarity.

**Q: Can subagents spawn their own subagents?**
A: No, this is prevented to avoid infinite recursion.

**Q: How long can a subagent run?**
A: Maximum 15 iterations (configurable). Long-running tasks may timeout.

**Q: Can I cancel a subagent?**
A: Not directly from CLI yet. Future enhancement planned.

**Q: Do subagents cost more API calls?**
A: Yes, each subagent makes its own LLM calls. But parallel execution saves total time.

**Q: Are results cached?**
A: Results are queued until retrieved via `check_subagent_results`, then cleared.

## See Also

- **Technical details**: [docs/NANOBOT_STYLE_INTEGRATION.md](NANOBOT_STYLE_INTEGRATION.md)
- **Implementation summary**: [NANOBOT_INTEGRATION_COMPLETE.md](../NANOBOT_INTEGRATION_COMPLETE.md)
- **Original subagent docs**: [docs/skills/subagents.md](skills/subagents.md)
- **Nanobot comparison**: [COMPARACION_NANOBOT.md](../COMPARACION_NANOBOT.md)

---

**Questions or Issues?**

If you encounter problems or have suggestions, please check the troubleshooting section above or refer to the technical documentation.
