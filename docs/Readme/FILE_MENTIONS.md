# File Mentions with @ Symbol

## Overview

DaveAgent now supports **file mentions** using the `@` symbol. This feature allows you to reference specific files in your queries, giving them **high priority** in the context when the AI processes your request.

## How It Works

When you type `@` followed by a file name or path, DaveAgent:

1. **Detects the @ symbol** in your input
2. **Indexes all files** in your project directory (excluding hidden files and common ignore patterns)
3. **Shows an interactive file selector** with:
   - Scrollable list of files with full paths
   - Real-time search/filtering
   - Keyboard navigation (arrow keys)
4. **Reads the selected file's content** and includes it with high priority in your request
5. **Sends the combined context** to the AI agent for processing

## Usage Examples

### Basic File Mention

```
@main.py fix the bug in the authentication logic
```

This will:
- Open the file selector filtered by "main.py"
- Let you navigate and select the exact file
- Include the full content of `main.py` in the context
- Send your request with the file content to the agent

### Multiple File Mentions

```
@config.py @utils.py refactor these two files to use dependency injection
```

Each `@` will trigger the file selector separately, allowing you to select multiple files.

### Partial Path Search

```
@agents/code explain how this file works
```

The file selector will filter files containing "agents/code" in their path.

### No Query (Browse All Files)

```
@
```

Just typing `@` with no text after it will show all indexed files for browsing.

## Interactive File Selector

When the file selector appears:

### Navigation
- **↑ / ↓ Arrow Keys**: Move selection up/down
- **Type characters**: Filter files in real-time
- **Enter**: Select the highlighted file
- **Esc**: Cancel selection
- **Backspace**: Remove characters from search query

### Display
```
📁 Select a file (Arrow keys to navigate, Enter to select, Esc to cancel)
Search: @main
────────────────────────────────────────────────────────────
▶ main.py
  src/main_helper.py
  tests/test_main.py






Showing 1-3 of 3 files (0%)
```

### Features
- Shows up to 10 files at a time
- Scrolls automatically as you navigate
- Shows current position and total count
- Full relative paths from project root

## File Context Format

When files are mentioned, their content is prepended to your request in this format:

```
📎 MENTIONED FILES CONTEXT (High Priority):

============================================================
FILE: src/config/settings.py
============================================================
[full file content here]
============================================================

============================================================
FILE: main.py
============================================================
[full file content here]
============================================================

USER REQUEST:
[your actual request here]
```

This ensures the AI has full context of the files you want to work with.

## Excluded Files

The file indexer automatically excludes:

### Hidden Files/Directories
- Anything starting with `.` (e.g., `.git`, `.env`, `.vscode`)

### Common Ignore Patterns
- `__pycache__`, `node_modules`, `venv`, `.venv`
- `dist`, `build`, `*.egg-info`
- `.pytest_cache`, `.mypy_cache`
- `logs`

### Binary/Media Files
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`
- Archives: `.zip`, `.tar`, `.gz`, `.rar`
- Executables: `.exe`, `.dll`, `.so`, `.dylib`
- Media: `.mp3`, `.mp4`, `.avi`, `.mov`
- Compiled: `.pyc`, `.pyo`

## Technical Details

### Components

1. **FileIndexer** (`src/utils/file_indexer.py`)
   - Scans directory tree
   - Filters out excluded patterns
   - Provides search functionality

2. **FileSelector** (`src/utils/file_selector.py`)
   - Interactive UI with ANSI terminal codes
   - Keyboard input handling (cross-platform)
   - Real-time rendering

3. **CLI Integration** (`src/interfaces/cli_interface.py`)
   - Detects `@` in user input
   - Manages mentioned files list
   - Reads file content for context

4. **Main Integration** (`main.py`)
   - Prepends file context to requests
   - Displays mentioned files to user
   - Passes combined context to agents

### Performance

- **Lazy indexing**: Files are only indexed on first `@` use
- **Cached index**: Subsequent `@` uses don't re-scan
- **Efficient search**: O(n) search through indexed file list
- **Memory efficient**: Only reads selected files, not all indexed files

## Tips & Best Practices

1. **Be specific**: Use `@src/agents/code` instead of `@code` to narrow results faster

2. **Multiple files**: You can mention multiple files in one request for comparative tasks

3. **Clear mentions**: Use `/new` command to start fresh and clear mentioned files

4. **Large files**: Be mindful that very large files will consume context tokens

5. **Verification**: After selection, DaveAgent shows which files were selected

## Examples

### Fix a Bug
```
@app.py there's a bug in the login function, fix it
```

### Compare Files
```
@old_implementation.py @new_implementation.py what are the differences?
```

### Explain Code
```
@src/agents/task_planner.py explain how this planner works
```

### Refactor
```
@utils.py @helpers.py merge these into a single module
```

### Add Feature
```
@main.py add a new command /export to export conversation history
```

## Troubleshooting

### File selector doesn't appear
- Make sure you have files in your project
- Check that files aren't all hidden/excluded

### Can't navigate with arrows
- Try installing `readchar`: `pip install readchar`
- On Windows, ensure console supports ANSI codes

### File not found after selection
- File paths are relative to project root
- Check file wasn't deleted/moved

### No files match search
- Try shorter search term
- Check spelling of file name

## Future Enhancements

Planned improvements:
- Remember recently selected files
- Fuzzy search matching
- File preview in selector
- Glob pattern support
- Directory selection
- Persistence across sessions
