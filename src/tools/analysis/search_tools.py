"""
Herramientas de búsqueda y análisis de código
"""
import os
import re
import subprocess
from pathlib import Path

WORKSPACE = Path(os.getcwd()).resolve()


async def grep_search(
    query: str,
    case_sensitive: bool = True,
    include_pattern: str = "*",
    max_results: int = 50
) -> str:
    """Busca un patrón de texto en archivos usando regex"""
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
            result += f"\n(Limited to {max_results} results)"

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
    """Busca definiciones de código (funciones, clases, variables)"""
    try:
        patterns = [
            rf"def\s+{query}\s*\(",
            rf"class\s+{query}\s*[\(:]",
            rf"function\s+{query}\s*\(",
            rf"const\s+{query}\s*=",
            rf"let\s+{query}\s*=",
            rf"var\s+{query}\s*=",
            rf"{query}\s*=\s*function",
            rf"public\s+\w+\s+{query}\s*\(",
            rf"private\s+\w+\s+{query}\s*\(",
            rf"\w+\s+{query}\s*\(",
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
            return f"No code definitions found for '{query}'"

        result = f"Found {len(matches)} code definition(s) for '{query}':\n"
        for file_path, line_num, line in matches:
            result += f"  {file_path}:{line_num}: {line[:100]}\n"

        return result
    except Exception as e:
        return f"Error searching codebase: {str(e)}"


async def run_terminal_cmd(command: str, require_user_approval: bool = False) -> str:
    """Ejecuta un comando de terminal"""
    dangerous_keywords = ['rm', 'del', 'format', 'shutdown', 'reboot', 'kill',
                          'pip install', 'npm install', 'apt-get', 'yum', 'curl', 'wget']

    is_dangerous = any(keyword in command.lower() for keyword in dangerous_keywords)

    if require_user_approval or is_dangerous:
        approval_msg = f"""
==================================================================
  COMMAND APPROVAL REQUIRED
==================================================================
  Command: {command[:50]}
  WARNING: This command requires user approval before execution
==================================================================
ACTION REQUIRED: Ask the user if they want to execute this command.
"""
        return approval_msg

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=WORKSPACE
        )

        output = f"Command: {command}\n"
        output += f"Exit code: {result.returncode}\n\n"

        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"

        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"

        return output

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after 60 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


async def diff_history(target_file: str = "", max_commits: int = 10) -> str:
    """Muestra el historial de diff de git"""
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
            return f"No git history found"

        output = f"Git history (last {max_commits} commits):\n"
        output += result.stdout

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
                lines = diff_result.stdout.split('\n')[:100]
                output += "\n\nLast change:\n" + '\n'.join(lines)
                if len(diff_result.stdout.split('\n')) > 100:
                    output += "\n... (output truncated)"

        return output

    except FileNotFoundError:
        return "Error: git is not installed"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out"
    except Exception as e:
        return f"Error getting diff history: {str(e)}"
