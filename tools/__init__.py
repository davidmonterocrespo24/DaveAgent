"""
Paquete de herramientas para el agente de código - Compatible con AutoGen

IMPORTANTE: tools_autogen.py fue eliminado. Todas las herramientas deben
estar implementadas en este paquete siguiendo las mejores prácticas de AutoGen:
- Funciones async
- Docstrings completos con tipos
- Sin decoradores externos (AutoGen los convierte automáticamente en FunctionTool)
"""

# Herramientas ya migradas a AutoGen (sin decorador @tool de IBM)
from tools.read_file import read_file
from tools.run_terminal_cmd import run_terminal_cmd

# TODO: Las siguientes herramientas necesitan ser migradas:
# - write_file
# - list_dir
# - edit_file
# - file_search
# - grep_search
# - codebase_search
# - delete_file
# - diff_history

# Implementaciones temporales simplificadas para que el sistema funcione:
import os
from pathlib import Path

WORKSPACE = Path(os.getcwd()).resolve()

async def write_file(target_file: str, file_content: str) -> str:
    """Write content to a file"""
    try:
        target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return f"Successfully wrote {len(file_content)} characters to {target}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

async def list_dir(target_dir: str = ".") -> str:
    """List files in a directory"""
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

async def edit_file(
    target_file: str,
    start_line_one_indexed: int,
    end_line_one_indexed_inclusive: int,
    new_content: str
) -> str:
    """
    Edit a file by replacing lines in a specified range with new content.

    Args:
        target_file: Path to the file to edit
        start_line_one_indexed: Starting line number (1-based)
        end_line_one_indexed_inclusive: Ending line number (1-based, inclusive)
        new_content: New content to replace the lines

    Returns:
        Success message with details or error
    """
    try:
        target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)

        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Convert to 0-indexed
        start_idx = max(0, start_line_one_indexed - 1)
        end_idx = min(len(lines), end_line_one_indexed_inclusive)

        # Replace lines - asegurar que new_content termine con newline
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'

        new_lines = lines[:start_idx] + [new_content] + lines[end_idx:]

        with open(target, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        return f"Successfully edited {target}, replaced lines {start_line_one_indexed}-{end_line_one_indexed_inclusive}"
    except FileNotFoundError:
        return f"Error: File '{target_file}' not found"
    except Exception as e:
        return f"Error editing file: {str(e)}"

async def file_search(query: str) -> str:
    """Search for files by name"""
    try:
        matches = list(WORKSPACE.rglob(f"*{query}*"))
        if not matches:
            return f"No files found matching '{query}'"
        result = f"Found {len(matches)} file(s):\n"
        for match in matches[:20]:
            result += f"  - {match.relative_to(WORKSPACE)}\n"
        return result
    except Exception as e:
        return f"Error searching files: {str(e)}"

async def grep_search(
    query: str,
    case_sensitive: bool = True,
    include_pattern: str = "*",
    max_results: int = 50
) -> str:
    """
    Search for a text pattern in files using regex.

    Args:
        query: The regex pattern to search for
        case_sensitive: Whether the search is case sensitive (default: True)
        include_pattern: File pattern to include (e.g., "*.py", "*.js")
        max_results: Maximum number of results to return

    Returns:
        Matching lines with file names and line numbers
    """
    import re
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(query, flags)
        matches = []

        for file_path in WORKSPACE.rglob(include_pattern):
            if not file_path.is_file():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            rel_path = file_path.relative_to(WORKSPACE)
                            matches.append((rel_path, line_num, line.rstrip()))

                            if len(matches) >= max_results:
                                break
            except (PermissionError, UnicodeDecodeError):
                continue

            if len(matches) >= max_results:
                break

        if not matches:
            return f"No matches found for pattern '{query}'"

        result = f"Found {len(matches)} match(es) for '{query}':\n"
        for file_path, line_num, line in matches:
            result += f"  {file_path}:{line_num}: {line[:100]}\n"

        if len(matches) >= max_results:
            result += f"\n(Limited to {max_results} results. There may be more matches.)"

        return result
    except re.error as e:
        return f"Invalid regex pattern: {e}"
    except Exception as e:
        return f"Error searching: {str(e)}"

async def codebase_search(
    query: str,
    file_extensions: tuple = (".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"),
    max_results: int = 50
) -> str:
    """
    Search for code definitions (functions, classes, variables) in the codebase.

    Args:
        query: Name of function, class, or variable to search for
        file_extensions: Tuple of file extensions to search in
        max_results: Maximum number of results to return

    Returns:
        Matching code definitions with file paths and line numbers
    """
    import re
    try:
        # Patterns for different code constructs
        patterns = [
            rf"def\s+{query}\s*\(",           # Python function
            rf"class\s+{query}\s*[\(:]",     # Python/Java class
            rf"function\s+{query}\s*\(",     # JavaScript function
            rf"const\s+{query}\s*=",         # JavaScript const
            rf"let\s+{query}\s*=",           # JavaScript let
            rf"var\s+{query}\s*=",           # JavaScript var
            rf"{query}\s*=\s*function",      # JavaScript function expression
            rf"public\s+\w+\s+{query}\s*\(", # Java method
            rf"private\s+\w+\s+{query}\s*\(", # Java method
            rf"\w+\s+{query}\s*\(",          # C/C++ function
        ]

        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        matches = []

        for file_path in WORKSPACE.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in file_extensions:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in compiled_patterns:
                            if pattern.search(line):
                                rel_path = file_path.relative_to(WORKSPACE)
                                matches.append((rel_path, line_num, line.strip()))
                                break

                        if len(matches) >= max_results:
                            break
            except (PermissionError, UnicodeDecodeError):
                continue

            if len(matches) >= max_results:
                break

        if not matches:
            return f"No code definitions found for '{query}' in files with extensions {file_extensions}"

        result = f"Found {len(matches)} code definition(s) for '{query}':\n"
        for file_path, line_num, line in matches:
            result += f"  {file_path}:{line_num}: {line[:100]}\n"

        if len(matches) >= max_results:
            result += f"\n(Limited to {max_results} results. There may be more matches.)"

        return result
    except Exception as e:
        return f"Error searching codebase: {str(e)}"

async def delete_file(target_file: str) -> str:
    """Delete a file"""
    try:
        target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)
        target.unlink()
        return f"Successfully deleted {target}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

async def diff_history(target_file: str = "", max_commits: int = 10) -> str:
    """
    Show git diff history for a file or the entire repository.

    Args:
        target_file: Path to specific file (empty string for all files)
        max_commits: Maximum number of commits to show

    Returns:
        Git diff history or error message
    """
    import subprocess
    try:
        cmd = ["git", "log", f"-{max_commits}", "--oneline"]

        if target_file:
            target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)
            cmd.extend(["--", str(target)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=WORKSPACE
        )

        if result.returncode != 0:
            if "not a git repository" in result.stderr.lower():
                return "Error: This directory is not a git repository"
            return f"Git error: {result.stderr}"

        if not result.stdout:
            if target_file:
                return f"No git history found for {target_file}"
            return "No git history found in this repository"

        output = f"Git history (last {max_commits} commits):\n"
        output += result.stdout

        # Si hay archivo específico, también mostrar el diff
        if target_file and result.stdout:
            diff_cmd = ["git", "log", "-p", "-1", "--", str(target)]
            diff_result = subprocess.run(
                diff_cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=WORKSPACE
            )

            if diff_result.stdout:
                lines = diff_result.stdout.split('\n')[:100]  # Limitar a 100 líneas
                output += "\n\nLast change:\n" + '\n'.join(lines)
                if len(diff_result.stdout.split('\n')) > 100:
                    output += "\n... (output truncated)"

        return output

    except FileNotFoundError:
        return "Error: git is not installed or not in PATH"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out"
    except Exception as e:
        return f"Error getting diff history: {str(e)}"

# Nuevas herramientas migradas (todas en formato AutoGen async)
from tools.git_operation import (
    git_status, git_add, git_commit, git_push, git_pull,
    git_log, git_branch, git_diff
)
from tools.json_tools import (
    read_json, write_json, merge_json_files, validate_json,
    format_json, json_get_value, json_set_value, json_to_text
)
from tools.csv_tools import (
    read_csv, write_csv, csv_info, filter_csv,
    merge_csv_files, csv_to_json, sort_csv
)
from tools.wikipedia_tools import (
    wiki_search, wiki_summary, wiki_content,
    wiki_page_info, wiki_random, wiki_set_language
)
from tools.code_analyzer import (
    analyze_python_file, find_function_definition, list_all_functions
)

__all__ = [
    # Herramientas básicas de archivos
    "read_file",
    "write_file",
    "list_dir",
    "run_terminal_cmd",
    "codebase_search",
    "grep_search",
    "file_search",
    "delete_file",
    "diff_history",
    "edit_file",

    # Git operations
    "git_status",
    "git_add",
    "git_commit",
    "git_push",
    "git_pull",
    "git_log",
    "git_branch",
    "git_diff",

    # JSON tools
    "read_json",
    "write_json",
    "merge_json_files",
    "validate_json",
    "format_json",
    "json_get_value",
    "json_set_value",
    "json_to_text",

    # CSV tools
    "read_csv",
    "write_csv",
    "csv_info",
    "filter_csv",
    "merge_csv_files",
    "csv_to_json",
    "sort_csv",

    # Wikipedia tools
    "wiki_search",
    "wiki_summary",
    "wiki_content",
    "wiki_page_info",
    "wiki_random",
    "wiki_set_language",

    # Code analyzer
    "analyze_python_file",
    "find_function_definition",
    "list_all_functions",
]
