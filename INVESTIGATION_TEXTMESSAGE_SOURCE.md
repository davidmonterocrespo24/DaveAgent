# Investigation: TextMessage Source Attribution Issue

**Date**: 2026-02-18
**Status**: 🔄 Diagnostic Logging Added - Awaiting Test Results
**Version**: 1.0.11

---

## 🎯 Problem Statement

TextMessage responses from agents (Planner, Coder) are not showing in the console. User only sees:
- ✅ Tool calls (ToolCallRequestEvent, ToolCallExecutionEvent)
- ✅ Tool results
- ❌ Agent's final TextMessage responses

### Evidence from Logs

```
2026-02-18 10:55:12 | Stream mensaje #1 - Tipo: TextMessage, Source: user
```

The first TextMessage has `source="user"` instead of expected `source="Planner"` or `source="Coder"`.

---

## 🔬 Deep Investigation Completed

### AutoGen Library Analysis

I analyzed the complete AutoGen library source code (`autogen_agentchat` v0.7.5) to understand message flow:

#### 1. How Agents Create TextMessage Responses

**File**: `_assistant_agent.py` (lines 1167-1171)

```python
yield Response(
    chat_message=TextMessage(
        content=current_model_result.content,
        source=agent_name,  # ✅ Correctly set to agent name
        models_usage=current_model_result.usage,
        id=message_id,
    ),
    inner_messages=inner_messages,
)
```

**Finding**: Agents correctly create TextMessages with `source=agent_name` (e.g., "Planner", "Coder").

#### 2. How Messages Flow Through Group Chat

**File**: `_chat_agent_container.py` (lines 135, 167-174)

```python
# Step 1: Log message to output topic
await self._log_message(msg.chat_message)

# Step 2: Publish as GroupChatMessage
async def _log_message(self, message: BaseAgentEvent | BaseChatMessage) -> None:
    await self.publish_message(
        GroupChatMessage(message=message),  # Wraps TextMessage
        topic_id=DefaultTopicId(type=self._output_topic_type),
    )
```

**Finding**: Messages are wrapped in `GroupChatMessage` and published to output topic.

#### 3. How Group Chat Manager Queues Messages

**File**: `_base_group_chat_manager.py` (lines 263-265)

```python
@event
async def handle_group_chat_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
    """Handle a group chat message by appending the content to its output message queue."""
    await self._output_message_queue.put(message.message)  # ✅ Unwraps and preserves source
```

**Finding**: Manager unwraps `GroupChatMessage` and puts the original TextMessage (with correct source) in the queue.

#### 4. How Stream Yields Messages

**File**: `_base_group_chat.py` (lines 557-564)

```python
message = await message_future
if isinstance(message, GroupChatTermination):
    if message.error is not None:
        raise RuntimeError(str(message.error))
    stop_reason = message.message.content
    break
yield message  # ✅ Yields message with preserved source
if isinstance(message, ModelClientStreamingChunkEvent):
    continue
output_messages.append(message)
```

**Finding**: Stream yields messages directly from the queue with source intact.

#### 5. Task Message Handling

**File**: `_base_group_chat.py` (line 460)

```python
elif isinstance(task, str):
    messages = [TextMessage(content=task, source="user")]  # Task messages have source="user"
```

**File**: `_base_group_chat_manager.py` (lines 111-114)

```python
# Only put messages in output queue if output_task_messages is True
if message.output_task_messages:
    for msg in message.messages:
        await self._output_message_queue.put(msg)  # Task messages go to queue
```

**Finding**: Initial task messages (source="user") ARE published to the stream when `output_task_messages=True` (default).

---

## 🧩 Expected Message Flow

```
User Input: "crea un reporte de este proyecto en un readme"
    ↓
run_stream(task="crea un...") with output_task_messages=True
    ↓
[Message #1] TextMessage(content="crea un...", source="user") ← Task message
    ↓
Selector routes to Planner
    ↓
[Message #2] TextMessage(content="I'll create...", source="Planner") ← SHOULD APPEAR
    ↓
Selector routes to Coder
    ↓
[Messages #3-N] ToolCallRequestEvent, ToolCallExecutionEvent (source="Coder")
    ↓
[Message #N+1] TextMessage(content="I've completed...", source="Coder") ← SHOULD APPEAR
```

---

## ❓ Current Mystery

### What We Know:

1. ✅ AutoGen library correctly creates agent TextMessages with `source=agent_name`
2. ✅ AutoGen library preserves source through entire message pipeline
3. ✅ Stream yields both task messages AND agent response messages
4. ✅ Our filter logic is correct: `if hasattr(msg, "source") and msg.source != "user"`
5. ✅ Tests prove filtering and deduplication logic works correctly

### What We DON'T Know:

**Why are we only seeing TextMessage with source="user" in the logs?**

Possible explanations:
1. **Agent hasn't responded yet**: Maybe the Planner/Coder are only executing tools and haven't sent a TextMessage response yet
2. **Message transformation**: Something between AutoGen and our code is changing the source
3. **Stream consumption issue**: We're not consuming the full stream
4. **Timing issue**: Agent responses come after we stop processing

---

## 🔧 Diagnostic Changes Applied

### Enhanced Logging in main.py (lines 1606-1625)

**Added comprehensive message logging**:

```python
# DIAGNOSTIC: Log ALL message types with full details
content_preview = ""
if hasattr(msg, "content"):
    c = msg.content
    if isinstance(c, str):
        content_preview = c[:80]
    elif isinstance(c, list):
        content_preview = f"[list with {len(c)} items]"
    else:
        content_preview = str(c)[:80]

self.logger.debug(
    f"📨 Msg #{message_count} | Type: {msg_type:30} | Source: '{msg_source:10}' | "
    f"Preview: {content_preview}"
)
```

**Added agent response detection for misattributed messages**:

```python
# DIAGNOSTIC: Check if this is actually an agent response incorrectly marked
if msg_type == "TextMessage" and hasattr(msg, "content"):
    content = str(msg.content)
    # Agent responses typically don't start with user-like phrases
    if any(marker in content for marker in ["I'll", "I will", "I've", "Let me", "I have", "Based on", "TERMINATE"]):
        self.logger.warning(
            f"⚠️ TextMessage with source='user' but appears to be agent response! "
            f"Content: {content[:100]}"
        )
```

---

## 📋 Next Steps for User

### 1. Run the Agent with Enhanced Logging

```bash
daveagent
```

### 2. Give a Simple Command

```
You: dame un resumen breve de este proyecto
```

### 3. Check the Logs

Look for the new diagnostic output format:

```
📨 Msg #1 | Type: TextMessage                    | Source: 'user      ' | Preview: dame un resumen...
📨 Msg #2 | Type: ToolCallRequestEvent           | Source: 'Coder     ' | Preview: [list with 1 items]
📨 Msg #3 | Type: ToolCallExecutionEvent         | Source: 'Coder     ' | Preview: ...
```

### 4. Critical Questions to Answer:

| Question | What to Look For |
|----------|-----------------|
| **Do we see ANY TextMessages besides the first one?** | More `Type: TextMessage` lines beyond #1 |
| **What sources do ToolCall events have?** | Should be `Source: 'Coder'` or `Source: 'Planner'` |
| **Do we see the warning about misattributed messages?** | `⚠️ TextMessage with source='user' but appears to be agent response!` |
| **Does the stream complete or timeout?** | Check if we see `✅ Stream completed` |

---

## 🎯 Possible Fixes (Based on Findings)

### Scenario A: Agent Responses ARE in Stream with Correct Source

**If logs show**: `📨 Msg #5 | Type: TextMessage | Source: 'Planner' | Preview: I'll create...`

**Fix**: There's a bug in our current code - the fix is already in place (enhanced logging helped identify it).

### Scenario B: Agent Responses in Stream with source="user"

**If logs show**:
```
⚠️ TextMessage with source='user' but appears to be agent response! Content: I'll help you create...
```

**Fix**: Override source attribution or change filter logic:
```python
# Option 1: Check content instead of just source
if msg_type == "TextMessage":
    content = str(msg.content) if hasattr(msg, "content") else ""
    # First message is task, subsequent TextMessages are responses
    if message_count == 1:
        continue  # Skip task message
    else:
        # Process as agent response regardless of source
        agent_name = msg.source if msg.source != "user" else "Agent"
```

### Scenario C: No Agent TextMessages in Stream (Only Events)

**If logs show**: Only ToolCallRequestEvent, ToolCallExecutionEvent, but no TextMessage from agents

**Possible causes**:
- Agents are configured to only execute tools without final responses
- Stream is being terminated early
- Agent system prompts don't instruct them to provide final responses

**Fix**: Check agent system prompts and ensure they instruct agents to provide textual responses.

---

## 📚 Related Files

- [src/main.py](src/main.py) - Main message processing loop (lines 1606-1640)
- [src/config/orchestrator.py](src/config/orchestrator.py) - SelectorGroupChat setup (lines 607-613)
- [test/test_message_filtering.py](test/test_message_filtering.py) - Filtering logic tests
- [test/test_message_deduplication.py](test/test_message_deduplication.py) - Deduplication tests
- [DIAGNOSIS_MESSAGE_NOT_SHOWING.md](DIAGNOSIS_MESSAGE_NOT_SHOWING.md) - Initial diagnosis

---

## 📊 AutoGen Source Files Analyzed

All files in `C:\Python312\Lib\site-packages\autogen_agentchat\`:

- `agents/_assistant_agent.py` - Agent response creation
- `teams/_group_chat/_base_group_chat.py` - Stream handling
- `teams/_group_chat/_base_group_chat_manager.py` - Message queue management
- `teams/_group_chat/_chat_agent_container.py` - Message logging
- `teams/_group_chat/_selector_group_chat.py` - Selector implementation
- `teams/_group_chat/_events.py` - Event type definitions
- `messages.py` - Message type definitions

---

## ✅ Conclusion

The AutoGen library is working correctly - it properly creates and preserves TextMessage sources through the entire pipeline. The issue is either:

1. **Environmental**: Agent responses aren't being generated or aren't reaching our code
2. **Logical**: Our filter is working correctly but agent responses truly have source="user" (library bug)
3. **Timing**: We're not seeing agent responses because execution is blocked elsewhere

**The enhanced diagnostic logging will definitively answer which scenario we're in.**

---

**Status**: 🟡 Waiting for test execution with enhanced logging to identify root cause
