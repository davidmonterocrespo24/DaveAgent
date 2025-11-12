# File Mentions Demo - Interactive Tutorial

## Scenario 1: Fix a Bug in a Specific File

**What you type:**
```
@main.py I'm getting an error when starting the app, can you check and fix it?
```

**What happens:**
1. File selector appears with files matching "main.py"
2. You see options like:
   ```
   ▶ main.py
     src/main_helper.py
     tests/test_main.py
   ```
3. You select `main.py` with Enter
4. CodeAgent shows:
   ```
   ✓ Selected: main.py

   📎 Mentioned Files:
     • main.py
   ```
5. The agent receives your request WITH the full content of `main.py`
6. Agent analyzes the file and suggests/applies fixes

## Scenario 2: Compare Two Implementations

**What you type:**
```
@v1/auth.py @v2/auth.py what are the key differences between these implementations?
```

**What happens:**
1. First `@` triggers selector for "v1/auth.py"
2. You select `v1/auth.py`
3. Second `@` triggers selector for "v2/auth.py"
4. You select `v2/auth.py`
5. CodeAgent shows:
   ```
   📎 Mentioned Files:
     • v1/auth.py
     • v2/auth.py
   ```
6. Agent compares both files and explains differences

## Scenario 3: Browse and Select Without Search

**What you type:**
```
@
```

**What happens:**
1. File selector appears with ALL files
2. You can scroll through entire project
3. Type to filter in real-time:
   - Type `agent` → shows only files with "agent" in path
   - Type `src` → shows only files in src directory
   - Backspace → removes filter
4. Navigate with arrows, select with Enter

## Scenario 4: Refactor Code Across Files

**What you type:**
```
@utils/database.py @models/user.py refactor the database connection to use a connection pool
```

**What happens:**
1. Select both files through the selector
2. CodeAgent receives full context of both files
3. Agent understands the current structure
4. Agent proposes refactoring with changes to both files
5. Implements the changes if you approve

## Scenario 5: Add Feature to Existing File

**What you type:**
```
@cli.py add a new command /export that exports the conversation to JSON
```

**What happens:**
1. Select `cli.py` (or `src/cli.py` depending on your project)
2. Agent reads the entire file structure
3. Agent understands existing commands
4. Agent adds the new `/export` command in the right place
5. Shows you the changes made

## Scenario 6: Explain Complex Code

**What you type:**
```
@src/agents/code_searcher.py explain how this agent works, especially the search_code_context method
```

**What happens:**
1. Select the file
2. Agent receives full file content
3. Agent provides detailed explanation:
   - Overall class structure
   - How `search_code_context` works
   - Dependencies and tools used
   - Examples of usage

## Advanced: Combining @ with /search

**Workflow:**
```
Step 1: /search authentication methods in the codebase

Step 2: Based on results, use @:
@src/auth/login.py @src/auth/jwt.py update these to use bcrypt for password hashing
```

**Benefits:**
- First, discover relevant files with `/search`
- Then, work on specific files with `@`
- Combines discovery with targeted action

## Tips for Effective Use

### 1. Use Specific Paths
❌ `@config` (too many matches)
✅ `@src/config/settings.py` (precise)

### 2. Verify Selection
Always check the "Mentioned Files" list after selection to ensure you selected the right files.

### 3. Clear Context When Needed
Start a new conversation with `/new` if you want to work on different files without the previous context.

### 4. Combine Multiple Files Wisely
```
✅ @model.py @test_model.py (related files)
❌ @file1.py @file2.py @file3.py @file4.py @file5.py (too many files, context overflow)
```

### 5. Use for High-Priority Context
The `@` feature is perfect when you need the agent to focus on specific files rather than searching the entire codebase.

## Keyboard Cheat Sheet

When file selector is open:

| Key | Action |
|-----|--------|
| ↑   | Move selection up |
| ↓   | Move selection down |
| Enter | Select highlighted file |
| Esc | Cancel selection |
| A-Z | Type to filter files |
| Backspace | Remove last filter character |
| Space | Add to search query |

## Common Patterns

### Pattern 1: Bug Fixing
```
@problematic_file.py there's a bug in line 45, the loop never terminates
```

### Pattern 2: Code Review
```
@new_feature.py review this code for security issues and best practices
```

### Pattern 3: Testing
```
@app.py write unit tests for all functions in this file
```

### Pattern 4: Documentation
```
@complex_algorithm.py add detailed docstrings to all functions
```

### Pattern 5: Optimization
```
@slow_function.py this function is too slow, optimize it
```

## Visual Flow Example

```
You type: @utils
           ↓
┌─────────────────────────────────────┐
│ 📁 Select a file                    │
│ Search: @utils                      │
│ ─────────────────────────────────   │
│ ▶ src/utils/__init__.py             │
│   src/utils/logger.py               │
│   src/utils/file_indexer.py         │
│   src/utils/file_selector.py        │
│   src/utils/setup_wizard.py         │
│   tests/test_utils.py               │
│                                     │
│ Showing 1-6 of 6 files             │
└─────────────────────────────────────┘
           ↓ [You press Enter]
✓ Selected: src/utils/__init__.py

📎 Mentioned Files:
  • src/utils/__init__.py

You continue typing: explain this file

           ↓
Agent receives:
─────────────────────────────────────
📎 MENTIONED FILES CONTEXT:
============================================
FILE: src/utils/__init__.py
============================================
[full file content]
============================================

USER REQUEST:
explain this file
─────────────────────────────────────
```

## Try It Yourself!

1. Start CodeAgent: `python -m src.cli`
2. Type: `@`
3. Navigate and select any file
4. Type your request
5. See the agent work with full file context!

---

**Pro Tip**: The more specific your `@` query, the faster you'll find your file! Instead of `@main`, try `@src/main` or even `@src/agents/main`.
