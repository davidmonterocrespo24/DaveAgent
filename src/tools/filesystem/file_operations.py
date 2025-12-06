"""
Operaciones de sistema de archivos - Consolidado
"""
import os
from pathlib import Path
import difflib

def get_workspace():
    """Get current workspace dynamically - respects os.chdir() for evaluations"""
    return Path(os.getcwd()).resolve()


async def read_file(target_file: str, should_read_entire_file: bool = True,
                   start_line_one_indexed: int = 1,
                   end_line_one_indexed_inclusive: int = -1) -> str:
    """
    Read the contents of a file with line range support.

    Args:
        target_file: Path to the file to be read
        should_read_entire_file: Whether to read the entire file or use line range
        start_line_one_indexed: Starting line number (1-based indexing)
        end_line_one_indexed_inclusive: Ending line number (1-based, inclusive). Use -1 for end of file.

    Returns:
        File contents with line range information, or error message if file not found
    """
    try:
        workspace = get_workspace()
        target_file = workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)

        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if should_read_entire_file:
            return f"File: {target_file}\n" + "".join(lines)

        # Convert to 0-indexed for Python
        start_idx = max(0, start_line_one_indexed - 1)
        if end_line_one_indexed_inclusive == -1:
            end_idx = len(lines)
        else:
            end_idx = min(len(lines), end_line_one_indexed_inclusive)

        selected_lines = lines[start_idx:end_idx]

        result = f"File: {target_file} (lines {start_line_one_indexed}-{end_idx})\n"
        if start_idx > 0:
            result += f"... {start_idx} lines above not shown ...\n"

        result += "".join(selected_lines)

        if end_idx < len(lines):
            result += f"... {len(lines) - end_idx} lines below not shown ...\n"

        return result
    except FileNotFoundError:
        return f"Error: File '{target_file}' not found"
    except Exception as e:
        return f"Error reading file: {str(e)}"


async def write_file(target_file: str, file_content: str) -> str:
    """Escribe contenido en un archivo"""
    try:
        workspace = get_workspace()
        target = workspace / target_file if not Path(target_file).is_absolute() else Path(target_file)
        target.parent.mkdir(parents=True, exist_ok=True)

        # --- SANITY CHECK: PREVENT OVERWRITE DEMOLITION ---
        if target.exists():
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                old_lines = len(old_content.splitlines())
                new_lines = len(file_content.splitlines())
                
                # Rule: If overwriting a large file (>200 lines) with a small one (<50 lines)
                if old_lines > 200 and new_lines < 50:
                    return f"Error: You are trying to overwrite a large file ({old_lines} lines) with very little content ({new_lines} lines). This looks like accidental data loss. If you meant to edit the file, use 'edit_file' instead. If you actually want to replace the file, delete it first using 'delete_file' and then write it."
            except Exception:
                # If we can't read the file (e.g. binary), skip check
                pass
        # --------------------------------------------------

        with open(target, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return f"Successfully wrote {len(file_content)} characters to {target}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


async def list_dir(target_dir: str = ".") -> str:
    """Lista archivos en un directorio"""
    try:
        workspace = get_workspace()
        target = workspace / target_dir if not Path(target_dir).is_absolute() else Path(target_dir)
        result = f"Directory listing for {target}:\n"
        for item in sorted(target.iterdir()):
            if item.is_dir():
                result += f"  [DIR]  {item.name}/\n"
            else:
                result += f"  [FILE] {item.name} ({item.stat().st_size} bytes)\n"
        return result
    except Exception as e:
        return f"Error listing directory: {str(e)}"


async def edit_file(target_file: str, instructions: str, code_edit: str) -> str:
    """
    Apply SURGICAL edits to an existing file using the // ... existing code ... marker system.

    STRATEGY:
    1. Extract context blocks (code before/after markers) from code_edit
    2. Find exact match location in original file using context
    3. Replace ONLY the matched section with new code
    4. Keep everything else untouched

    Parameters:
        target_file (str): Path to the file to be edited
        instructions (str): Description of the changes to be made
        code_edit (str): The new code with markers indicating context
        explanation (str): Optional explanation for the edit operation

    Returns:
        str: Success message with edit summary or error message if operation failed
    """
    try:
        # Read the current file
        with open(target_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        original_lines = original_content.split('\n')
        edit_lines = code_edit.split('\n')

        # Patterns that indicate "existing code" markers in various languages
        marker_patterns = [
            "... existing code ...",
            "existing code",
            "resto del código",
            "código existente"
        ]

        def is_marker_line(line: str) -> bool:
            """Check if line is an 'existing code' marker"""
            line_stripped = line.strip()
            for marker in marker_patterns:
                if marker in line_stripped.lower():
                    return True
            return False

        # STEP 1: Extract context blocks from code_edit
        # We need to find the FIRST non-marker block (context before edit)
        # and the LAST non-marker block (context after edit)

        context_before = []
        context_after = []
        edited_content = []

        found_first_marker = False

        i = 0
        while i < len(edit_lines):
            line = edit_lines[i]

            if is_marker_line(line):
                if not found_first_marker:
                    # This is the FIRST marker - everything before is context_before
                    found_first_marker = True
                else:
                    # This is a marker AFTER the edit section started
                    # Everything after this until next non-marker is context_after
                    # Collect remaining non-marker lines as context_after
                    for j in range(i + 1, len(edit_lines)):
                        if not is_marker_line(edit_lines[j]) and edit_lines[j].strip():
                            context_after.append(edit_lines[j])
                        elif is_marker_line(edit_lines[j]):
                            break
                    break
                i += 1
                continue

            if not found_first_marker:
                # Before first marker = context before edit
                if line.strip():
                    context_before.append(line)
            else:
                # After first marker but before last = actual edit
                edited_content.append(line)

            i += 1

        # STEP 2: Find the location in original file using context
        # We look for a sequence of lines matching context_before

        if not context_before:
            # No context provided - this is risky but we'll try to match edited_content
            return await _fallback_edit(target_file, original_lines, edited_content)

        # Find where context_before appears in original file
        match_start_idx = -1
        context_len = len(context_before)

        for idx in range(len(original_lines) - context_len + 1):
            # Check if lines match (with flexible whitespace)
            matches = True
            for ctx_idx, ctx_line in enumerate(context_before):
                orig_line = original_lines[idx + ctx_idx]
                # Compare stripped versions for flexibility
                if ctx_line.strip() != orig_line.strip():
                    matches = False
                    break

            if matches:
                match_start_idx = idx
                break

        if match_start_idx == -1:
            # Context not found - fallback to simpler strategy
            return await _fallback_edit(target_file, original_lines, edited_content)

        # STEP 3: Find where context_after appears (if provided)
        match_end_idx = len(original_lines)

        if context_after:
            # Look for context_after starting from after context_before
            context_after_len = len(context_after)
            for idx in range(match_start_idx + context_len, len(original_lines) - context_after_len + 1):
                matches = True
                for ctx_idx, ctx_line in enumerate(context_after):
                    orig_line = original_lines[idx + ctx_idx]
                    if ctx_line.strip() != orig_line.strip():
                        matches = False
                        break

                if matches:
                    match_end_idx = idx
                    break

        # STEP 4: Build new content with surgical replacement
        new_lines = []

        # Keep everything before the match
        new_lines.extend(original_lines[:match_start_idx])

        # Add context_before (preserved)
        new_lines.extend(context_before)

        # Add edited content
        new_lines.extend(edited_content)

        # Add context_after (preserved)
        new_lines.extend(context_after)

        # Keep everything after the match
        if match_end_idx + len(context_after) < len(original_lines):
            new_lines.extend(original_lines[match_end_idx + len(context_after):])

        new_content = '\n'.join(new_lines)

        # Generate unified diff
        diff = difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"{target_file} (original)",
            tofile=f"{target_file} (modified)",
            lineterm=''
        )
        diff_list = list(diff)
        diff_text = ''.join(diff_list)

        # --- SANITY CHECK: PREVENT FILE DEMOLITION ---
        # Count lines starting with '-' (deleted) and '+' (added), ignoring headers (---/+++)
        # We use a heuristic: excessive deletion with minimal addition is suspicious.
        deleted_lines_count = sum(1 for line in diff_list if line.startswith('-') and not line.startswith('---'))
        added_lines_count = sum(1 for line in diff_list if line.startswith('+') and not line.startswith('+++'))

        # Thresholds: >400 deleted AND <20 added (Net loss of >380 lines in a big chunk)
        if deleted_lines_count > 400 and added_lines_count < 20:
             return f"Error: Your edit would delete {deleted_lines_count} lines but only add {added_lines_count}. This looks like accidental file demolition (deleting code without replacement). Please use SURGICAL EDITS to change ONLY the necessary lines. Do not verify/rewrite the whole file content."
        # ---------------------------------------------

        # Write the new content
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Format the result with diff
        result = f"[OK] Successfully edited file: {target_file}\n"
        result += f"Instructions: {instructions}\n"
        result += f"Edit location: lines {match_start_idx + 1} to {match_end_idx + len(context_after)}\n"
        result += f"Original lines: {len(original_lines)} -> New lines: {len(new_lines)}\n\n"

        if diff_text:
            result += "===============================================================\n"
            result += "DIFF (Changes Applied):\n"
            result += "===============================================================\n"
            result += diff_text
            result += "\n===============================================================\n"

        return result

    except FileNotFoundError:
        return f"Error: File '{target_file}' not found"
    except Exception as e:
        return f"Error editing file: {str(e)}\n\nPlease provide more context around the code to edit."


async def _fallback_edit(target_file: str, original_lines: list, edited_content: list) -> str:
    """
    Fallback strategy when context matching fails.
    Tries to find edited_content directly in original file.
    """
    # Try to find first line of edited_content in original
    if not edited_content:
        return f"Error: No edited content provided in code_edit parameter"

    first_edit_line = next((line for line in edited_content if line.strip()), None)
    if not first_edit_line:
        return f"Error: No non-empty lines in edited content"

    # Search for this line in original
    match_idx = -1
    for idx, orig_line in enumerate(original_lines):
        if first_edit_line.strip() in orig_line or orig_line.strip() == first_edit_line.strip():
            match_idx = idx
            break

    if match_idx == -1:
        return f"Error: Could not locate edit position in file. Please provide more context lines before and after the edit."

    # Replace from match_idx for len(edited_content) lines
    new_lines = []
    new_lines.extend(original_lines[:match_idx])
    new_lines.extend(edited_content)
    new_lines.extend(original_lines[match_idx + len(edited_content):])

    new_content = '\n'.join(new_lines)

    # Write the new content
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return f"[OK] Edited file: {target_file} (fallback mode - matched at line {match_idx + 1})\nNote: Context matching failed, used fallback strategy. Consider providing more context."


async def delete_file(target_file: str, explanation: str = "") -> str:
    """
    Delete a file at the specified path.
    
    Parameters:
        target_file (str): The path to the file to be deleted
        explanation (str): Optional explanation for the deletion operation
    
    Returns:
        str: Success message if file deleted, error message if not found or failed
    """
    try:
        if os.path.exists(target_file):
            os.remove(target_file)
            return f"Successfully deleted file: {target_file}"
        else:
            return f"File not found: {target_file}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


async def file_search(query: str, explanation: str = "") -> str:
    """
    Fast file search based on fuzzy matching against file path.
    
    Parameters:
        query (str): Search term to match against file paths
        explanation (str): Optional explanation for the search operation
    
    Returns:
        str: List of matching file paths (up to 10 results) or error message if search failed
    """
    try:
        matches = []
        for root, dirs, files in os.walk("."):
            for file in files:
                file_path = os.path.join(root, file)
                if query.lower() in file_path.lower():
                    matches.append(file_path)
                    if len(matches) >= 10:  # Cap at 10 results
                        break
            if len(matches) >= 10:
                break
        
        return f"File search results for '{query}':\n" + "\n".join(matches)
    except Exception as e:
        return f"Error in file search: {str(e)}"