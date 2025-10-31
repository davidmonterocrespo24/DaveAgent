import os
from typing import Union
from pathlib import Path

# Usar el directorio actual como workspace
WORKSPACE = Path(os.getcwd()).resolve()

def to_workspace_path(path_like: Union[str, Path]) -> Path:
    """Convierte una ruta a absoluta desde el workspace actual"""
    p = Path(path_like)
    if not p.is_absolute():
        p = WORKSPACE / p
    p = p.resolve()
    return p

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
    target_file = to_workspace_path(target_file)
    try:
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
    

