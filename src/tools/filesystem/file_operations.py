"""
Operaciones de sistema de archivos - Consolidado
"""
import os
from pathlib import Path

WORKSPACE = Path(os.getcwd()).resolve()


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
        target_file = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)

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
        target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return f"Successfully wrote {len(file_content)} characters to {target}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


async def list_dir(target_dir: str = ".") -> str:
    """Lista archivos en un directorio"""
    try:
        target = WORKSPACE / target_dir if not Path(target_dir).is_absolute() else Path(target_dir)
        result = f"Directory listing for {target}:\n"
        for item in sorted(target.iterdir()):
            if item.is_dir():
                result += f"  [DIR]  {item.name}/\n"
            else:
                result += f"  [FILE] {item.name} ({item.stat().st_size} bytes)\n"
        return result
    except Exception as e:
        return f"Error listing directory: {str(e)}"


async def edit_file(target_file: str, instructions: str, code_edit: str, explanation: str = "") -> str:
    """
    Apply edits to an existing file using the // ... existing code ... marker system.
    
    Parameters:
        target_file (str): Path to the file to be edited
        instructions (str): Description of the changes to be made
        code_edit (str): The new code content with markers indicating where existing code should be preserved
        explanation (str): Optional explanation for the edit operation
    
    Returns:
        str: Success message with edit summary or error message if operation failed
    """
    try:
        # Read the current file
        with open(target_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Parse the code_edit to find the edits and markers
        lines = code_edit.split('\n')
        new_content = ""
        original_lines = original_content.split('\n')
        current_line_index = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this is an "existing code" marker
            if "... existing code ..." in line or "existing code" in line:
                # Find the next non-marker line to determine how much to skip
                next_edit_line = None
                for j in range(i + 1, len(lines)):
                    if "... existing code ..." not in lines[j] and lines[j].strip():
                        next_edit_line = lines[j]
                        break
                
                # If we have a next edit line, find it in the original content
                if next_edit_line:
                    # Look for the next edit line in the original content
                    found_index = -1
                    for k in range(current_line_index, len(original_lines)):
                        if next_edit_line.strip() in original_lines[k] or original_lines[k].strip() == next_edit_line.strip():
                            found_index = k
                            break
                    
                    if found_index != -1:
                        # Add the skipped original lines
                        for k in range(current_line_index, found_index):
                            new_content += original_lines[k] + '\n'
                        current_line_index = found_index
                    else:
                        # If we can't find the next line, add some original content
                        skip_lines = min(5, len(original_lines) - current_line_index)
                        for k in range(current_line_index, current_line_index + skip_lines):
                            if k < len(original_lines):
                                new_content += original_lines[k] + '\n'
                        current_line_index += skip_lines
                else:
                    # No next edit line found, skip to end or add remaining original content
                    remaining_lines = min(10, len(original_lines) - current_line_index)
                    for k in range(current_line_index, current_line_index + remaining_lines):
                        if k < len(original_lines):
                            new_content += original_lines[k] + '\n'
                    current_line_index += remaining_lines
                
            elif line and not ("..." in line and "existing" in line):
                # This is actual new/edited code
                new_content += lines[i] + '\n'
                current_line_index += 1
            
            i += 1
        
        # Add any remaining original content
        while current_line_index < len(original_lines):
            new_content += original_lines[current_line_index] + '\n'
            current_line_index += 1
        
        
        
        # Write the new content
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content.rstrip('\n') + '\n')
        
        return f"""
Successfully edited file: {target_file}
Instructions applied: {instructions}
Original lines: {len(original_lines)}
New lines: {len(new_content.split('\n'))}
Changes applied successfully!
        """
        
    except FileNotFoundError:
        return f"Error: File '{target_file}' not found"
    except Exception as e:
        return f"Error editing file: {str(e)}"


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