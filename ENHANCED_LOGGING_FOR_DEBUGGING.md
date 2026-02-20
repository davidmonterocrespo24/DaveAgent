# Enhanced Logging for Debugging - Agent Differentiation & Message Tracking

**Date**: 2026-02-19 (Updated)
**Version**: 1.0.12
**Purpose**: Differentiate main agent from subagents in logs AND track full message flow

---

## 🎯 Problem Solved

**Before**: Logs didn't distinguish between:
- Main agent's Coder
- Subagent #1's Coder
- Subagent #2's Coder

**After**: All logs now prefixed with unique agent ID:
```
[MAIN] Spawning subagent...
[SUB-7f3a2b1c] Starting subagent execution
[SUB-7f3a2b1c] [Selector] msg[0] from=user...
[SUB-9e4d1a5f] Task completed successfully
```

---

## 🔧 Changes Applied

### 1. Unique Agent IDs

**File**: `src/config/orchestrator.py:48-77`

**Added**:
```python
def __init__(
    self,
    *,
    debug: bool = False,
    api_key: str = None,
    base_url: str = None,
    model: str = None,
    ssl_verify: bool = None,
    headless: bool = False,
    agent_id: str = None,  # NEW: Unique identifier
):
    # Unique agent identifier (for distinguishing main agent from subagents in logs)
    import uuid
    self.agent_id = agent_id if agent_id else "MAIN"
    self.is_subagent = agent_id is not None  # True if this is a subagent

    # Log orchestrator initialization with ID
    self.logger.debug(f"[{self.agent_id}] Orchestrator initialized (headless={headless}, subagent={self.is_subagent})")
```

**Effect**:
- Main agent: `agent_id = "MAIN"`
- Subagents: `agent_id = "SUB-7f3a2b1c"` (8-char UUID)

---

### 2. Subagent Factory Enhanced Logging

**File**: `src/config/orchestrator.py:650-721`

**Added**:
```python
def _create_subagent_orchestrator(
    self,
    tools: list,
    max_iterations: int,
    mode: str = "subagent",
    task: str = "",
    subagent_id: str = None  # NEW: Unique identifier for logging
):
    # Generate subagent ID if not provided
    if not subagent_id:
        import uuid
        subagent_id = f"SUB-{str(uuid.uuid4())[:8]}"

    # Log subagent creation (DEBUG only - not shown in terminal)
    self.logger.debug(f"[{self.agent_id}] Creating subagent orchestrator with ID: {subagent_id}")
    self.logger.debug(f"[{self.agent_id}] Subagent task: {task[:100]}...")

    # Create orchestrator with unique ID
    subagent_orch = AgentOrchestrator(
        api_key=self.settings.api_key,
        base_url=self.settings.base_url,
        model=self.settings.model,
        ssl_verify=self.settings.ssl_verify,
        headless=True,
        agent_id=subagent_id,  # Pass unique ID for logging
    )

    # Log tool configuration (DEBUG only)
    tool_names = [t.name if hasattr(t, 'name') else str(t) for t in tools]
    self.logger.debug(f"[{subagent_id}] Configured with tools: {', '.join(tool_names)}")
    self.logger.debug(f"[{subagent_id}] Max tool iterations: {max_iterations}")

    # ... rest of factory code ...

    self.logger.debug(f"[{subagent_id}] Subagent orchestrator creation complete")
    return subagent_orch
```

**Effect**: Complete visibility into subagent creation process

---

### 3. Selector Logging Enhancement

**File**: `src/config/orchestrator.py:549-622`

**Updated ALL selector logs**:
```python
def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
    # Enhanced logging with agent_id prefix
    self.logger.debug(
        f"🔄 [{self.agent_id}] [Selector] msg[{len(messages)-1}] from={last_message.source} "
        f"type={type(last_message).__name__}: {content_preview}"
    )

    if last_message.source == "Planner":
        self.logger.debug(f"🔄 [{self.agent_id}] [Selector] Planner just spoke -> Selecting Coder (MANDATORY)")
        return "Coder"

    # ... all other selector logs also prefixed with [{self.agent_id}]
```

**Effect**: Know which agent (main or subagent) is making routing decisions

---

### 4. Subagent Manager Lifecycle Logging

**File**: `src/subagents/manager.py:114-255`

**Added detailed logging at each lifecycle stage**:

#### A. Spawn Phase
```python
# Log subagent spawn (DEBUG only - detailed logging for files)
self.logger.debug(f"[MAIN] Spawning subagent: ID={subagent_id}, label='{label}'")
self.logger.debug(f"[MAIN] Subagent task: {task[:200]}...")
self.logger.debug(f"[MAIN] Max iterations: {max_iterations}, Parent task: {parent_task_id}")
```

#### B. Execution Start
```python
self.logger.debug(f"[{subagent_id}] Starting subagent execution")
self.logger.debug(f"[{subagent_id}] Task: {task}")
self.logger.debug(f"[{subagent_id}] Label: '{label}', Max iterations: {max_iterations}")
self.logger.debug(f"[{subagent_id}] Created isolated toolset with {len(isolated_tools)} tools")
```

#### C. Task Execution
```python
self.logger.debug(f"[{subagent_id}] Orchestrator created, starting task execution...")
# ... task runs ...
self.logger.debug(f"[{subagent_id}] Task completed successfully")
```

#### D. Success
```python
self.logger.debug(f"[{subagent_id}] Result length: {len(result)} chars")
self.logger.debug(f"[{subagent_id}] Result preview: {result[:200]}...")
```

#### E. Failure
```python
self.logger.error(f"[{subagent_id}] Subagent failed with error: {type(e).__name__}: {str(e)}")
self.logger.debug(f"[{subagent_id}] Full traceback:", exc_info=True)
```

---

## 📊 Example Log Output

### Main Agent Workflow
```
[MAIN] Orchestrator initialized (headless=False, subagent=False)
[MAIN] 📨 User request length: 96 chars
[MAIN] 🚀 Stream task started
🔄 [MAIN] [Selector] msg[0] from=user type=TextMessage: crea un reporte...
🔄 [MAIN] [Selector] User message -> Starting with Planner
[MAIN] 📨 Msg #1 | Type: TextMessage | Source: 'user' | Preview: ...
[MAIN] 📨 Msg #2 | Type: TextMessage | Source: 'Planner' | Preview: PLAN: ...
🔄 [MAIN] [Selector] Planner just spoke -> Selecting Coder (MANDATORY)
[MAIN] 📨 Msg #3 | Type: ToolCallRequestEvent | Source: 'Coder' | Preview: ...
[MAIN] 🔧 Tool call: list_dir
[MAIN] Spawning subagent: ID=7f3a2b1c, label='readme-creator'
[MAIN] Subagent task: Create comprehensive README...
```

### Subagent Workflow (Parallel)
```
[SUB-7f3a2b1c] Starting subagent execution
[SUB-7f3a2b1c] Task: Create comprehensive README for this project
[SUB-7f3a2b1c] Label: 'readme-creator', Max iterations: 15
[SUB-7f3a2b1c] Created isolated toolset with 25 tools
[MAIN] Creating subagent orchestrator with ID: SUB-7f3a2b1c
[SUB-7f3a2b1c] Orchestrator initialized (headless=True, subagent=True)
[SUB-7f3a2b1c] Configured with tools: read_file, write_file, edit_file, ...
[SUB-7f3a2b1c] Max tool iterations: 15
[SUB-7f3a2b1c] Custom system prompt applied
[SUB-7f3a2b1c] Subagent orchestrator creation complete
[SUB-7f3a2b1c] Orchestrator created, starting task execution...
🔄 [SUB-7f3a2b1c] [Selector] No messages yet -> Starting with Coder
🔄 [SUB-7f3a2b1c] [Selector] msg[0] from=user type=TextMessage: Create comprehensive...
🔄 [SUB-7f3a2b1c] [Selector] User message -> Starting with Planner
[SUB-7f3a2b1c] 📨 Msg #1 | Type: TextMessage | Source: 'user' | Preview: ...
[SUB-7f3a2b1c] 📨 Msg #2 | Type: ToolCallRequestEvent | Source: 'Coder' | Preview: ...
[SUB-7f3a2b1c] Task completed successfully
[SUB-7f3a2b1c] Result length: 1245 chars
[SUB-7f3a2b1c] Result preview: README created with sections...
```

### Multiple Subagents Running Concurrently
```
[MAIN] Spawning subagent: ID=7f3a2b1c, label='readme-creator'
[MAIN] Spawning subagent: ID=9e4d1a5f, label='test-runner'
[MAIN] Spawning subagent: ID=2b8c5f3a, label='doc-generator'

[SUB-7f3a2b1c] Starting subagent execution
[SUB-9e4d1a5f] Starting subagent execution
[SUB-2b8c5f3a] Starting subagent execution

🔄 [SUB-7f3a2b1c] [Selector] msg[0] from=user...
🔄 [SUB-9e4d1a5f] [Selector] msg[0] from=user...
🔄 [SUB-2b8c5f3a] [Selector] msg[0] from=user...

[SUB-9e4d1a5f] Task completed successfully  ← Finished first
[SUB-7f3a2b1c] Task completed successfully  ← Finished second
[SUB-2b8c5f3a] Task completed successfully  ← Finished last
```

---

## 🔍 Debugging Workflow

### Finding Main Agent Issues
```bash
grep "\[MAIN\]" logs/daveagent_*.log
```

**Example output**:
```
[MAIN] Orchestrator initialized
[MAIN] User request: analyze project...
[MAIN] Spawning subagent: ID=7f3a2b1c
```

### Finding Specific Subagent
```bash
grep "\[SUB-7f3a2b1c\]" logs/daveagent_*.log
```

**Example output**:
```
[SUB-7f3a2b1c] Starting subagent execution
[SUB-7f3a2b1c] Task: Create README...
[SUB-7f3a2b1c] Tool call: read_file
[SUB-7f3a2b1c] Task completed successfully
```

### Comparing Selector Decisions
```bash
grep "Selector" logs/daveagent_*.log
```

**Example output**:
```
🔄 [MAIN] [Selector] Planner just spoke -> Selecting Coder
🔄 [SUB-7f3a2b1c] [Selector] Coder waiting for tool result -> Keep Coder
🔄 [SUB-9e4d1a5f] [Selector] User message -> Starting with Planner
```

### Tracking Subagent Lifecycle
```bash
grep "SUB-7f3a2b1c" logs/daveagent_*.log | grep -E "(Starting|completed|failed)"
```

**Example output**:
```
[SUB-7f3a2b1c] Starting subagent execution
[SUB-7f3a2b1c] Task completed successfully
```

---

## 🆕 NEW: Full Message Tracking (2026-02-19)

### 1. Complete Message Content Logging

**File**: `src/main.py` lines ~1643-1654

**What it logs**: FULL content of all `TextMessage` and `ThoughtEvent` messages

**Format**:
```
📬 FULL MESSAGE RECEIVED:
   Type: TextMessage
   Source: Coder
   Content:
I've analyzed the JAR file and extracted all resources...
   ================================================================================
```

**Level**: INFO (always visible)

---

### 2. Processing Decision Logging

**File**: `src/main.py` line ~1702

**What it logs**: When a message will be processed and shown in terminal

**Format**:
```
✅ Processing message (will show in terminal): TextMessage from Coder
```

**Level**: INFO

---

### 3. Skipped Message Logging

**File**: `src/main.py` lines ~1679-1707

**What it logs**: Messages that are filtered/skipped and why

**Formats**:
```
⏭️  Skipping message: TextMessage (source is 'user')
⏭️  Skipping duplicate message: TextMessage from Coder (already shown)
```

**Level**: DEBUG

---

### 4. Terminal Display Logging

**File**: `src/main.py` lines ~2029, ~2041

**What it logs**: When a message is actively being shown in the terminal

**Formats**:
```
🖥️  SHOWING IN TERMINAL (reasoning): Let me analyze...
🖥️  SHOWING IN TERMINAL (final response): I've completed the analysis...
```

**Level**: INFO

---

## 🔍 Debugging Missing Messages

### Command: Find ALL messages received
```bash
grep "📬 FULL MESSAGE RECEIVED" logs/daveagent_*.log
```

### Command: Find messages shown in terminal
```bash
grep "🖥️  SHOWING IN TERMINAL" logs/daveagent_*.log
```

### Command: Find why messages were skipped
```bash
grep "⏭️  Skipping" logs/daveagent_*.log
```

### Example Debugging Flow

**Problem**: "No veo la respuesta final del agente"

**Step 1**: Check if message was received
```bash
grep -A 5 "📬 FULL MESSAGE" logs/daveagent_*.log | tail -20
```

**Step 2**: Check if it was processed
```bash
grep "✅ Processing message" logs/daveagent_*.log | tail -10
```

**Step 3**: Check if it was shown
```bash
grep "🖥️  SHOWING" logs/daveagent_*.log | tail -10
```

**Step 4**: Check if it was skipped
```bash
grep "⏭️  Skipping" logs/daveagent_*.log | tail -10
```

---

## 📋 Log Levels

### DEBUG (File Only)
All the enhanced logs go to DEBUG level, so they:
- ✅ **Appear in log files** for detailed debugging
- ❌ **DO NOT appear in terminal** (clean UX)

### INFO (Terminal + File)
Progress logs visible to user:
```
📊 Progress: 20 tool calls completed, 40 messages processed
💾 Auto-save: State saved successfully
```

### ERROR (Terminal + File)
Errors from both main and subagents:
```
[SUB-7f3a2b1c] Subagent failed with error: FileNotFoundError: ...
```

---

## 🎯 Benefits

### 1. Clear Attribution
Know exactly which agent (main or subagent) is doing what

### 2. Parallel Execution Tracking
See multiple subagents working simultaneously without confusion

### 3. Issue Isolation
Quickly identify if a problem is in:
- Main agent logic
- Specific subagent
- Selector routing
- Tool execution

### 4. Performance Analysis
Compare execution patterns between main agent and subagents

### 5. Clean Terminal
All detailed logging goes to files, terminal stays clean

---

## 🔧 Configuration

### Viewing Debug Logs
```bash
# Watch logs in real-time
tail -f ~/.daveagent/logs/daveagent_YYYYMMDD.log

# Filter for specific agent
tail -f ~/.daveagent/logs/daveagent_*.log | grep "\[SUB-"

# Filter for main agent only
tail -f ~/.daveagent/logs/daveagent_*.log | grep "\[MAIN\]"
```

### Enabling More Verbose Logging
```bash
# Run with debug flag
daveagent --debug

# This enables:
# - All DEBUG logs in files
# - More detailed console output
# - Full tracebacks on errors
```

---

## 📊 Summary of Changes

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `src/config/orchestrator.py` | ~50 lines | Add agent_id to all logs |
| `src/subagents/manager.py` | ~30 lines | Lifecycle logging for subagents |
| Total DEBUG logs added | ~80 | Full execution transparency |

**Impact on Terminal**: NONE (all DEBUG logs)
**Impact on Log Files**: Comprehensive debugging information
**Impact on Performance**: Negligible (logging is fast)

---

## ✅ Testing

### Reinstall
```bash
cd E:\AI\CodeAgent
pip install -e .
```

### Test Main Agent
```bash
daveagent
```
```
You: analiza este proyecto
```

**Check logs**:
```bash
grep "\[MAIN\]" ~/.daveagent/logs/daveagent_*.log | tail -20
```

### Test Subagents
```
You: en segundo plano crea un README y corre los tests
```

**Check logs**:
```bash
# See all subagent activity
grep "\[SUB-" ~/.daveagent/logs/daveagent_*.log

# See specific subagent
grep "\[SUB-7f3a2b1c\]" ~/.daveagent/logs/daveagent_*.log
```

---

## 🎉 Result

**Before**:
```
🔄 [Selector] msg[0] from=user...
🔄 [Selector] msg[0] from=user...
```
❓ Which agent is this? Main or subagent?

**After**:
```
🔄 [MAIN] [Selector] msg[0] from=user...
🔄 [SUB-7f3a2b1c] [Selector] msg[0] from=user...
```
✅ Crystal clear which agent is which!

---

**Status**: 🟢 Ready to test - Enhanced logging provides full execution transparency
