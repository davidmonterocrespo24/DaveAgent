"""
Herramientas de búsqueda y análisis de código
"""

import os
import re
import subprocess
from pathlib import Path
import glob
import fnmatch
from typing import List, Optional
import concurrent.futures as cf
import re
from pathlib import Path
from typing import List, Optional, Sequence
WORKSPACE = Path(os.getcwd()).resolve()

# --------------------------------------------------------------------------- #
# Configuración interna
# --------------------------------------------------------------------------- #
DEFAULT_EXTS: Sequence[str] = (
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".h",
)  # extensiones a inspeccionar
MAX_RESULTS: int = 50  # tope de paths devueltos
CASE_SENSITIVE: bool = False  # búsqueda case-insensitive


# --------------------------------------------------------------------------- #
# Implementación auxiliar
# --------------------------------------------------------------------------- #
def _iter_code_files(roots: Sequence[Path], exts: Sequence[str]) -> list[Path]:
    """Recorre recursivamente los directorios dados devolviendo paths con extensiones deseadas."""
    paths: list[Path] = []
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                paths.append(p)
    return paths


def _file_contains(pattern: re.Pattern[str], path: Path) -> Optional[Path]:
    """Devuelve el propio path si contiene la coincidencia; None en caso contrario/exception."""
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            if any(pattern.search(line) for line in f):
                return path
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------- #


async def grep_search(
    query, case_sensitive=True, include_pattern=None, exclude_pattern=None, explanation=None
) -> str:
    """
    Search for a regex pattern in files using inclusion and exclusion filters.

    Parameters:
        query (str): The regex pattern to search for
        case_sensitive (bool): Whether the search should be case-sensitive
        include_pattern (str): Glob pattern for files to include (e.g., '*.py')
        exclude_pattern (str): Glob pattern for files to exclude
        explanation (str): One-sentence explanation of the search purpose

    Returns:
        list: List of dictionaries with search results including file path, line number, and matches
    """
    results = []

    # Configurar flags para regex
    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        # Compilar el patrón regex
        pattern = re.compile(query, flags)
    except re.error as e:
        return [{"error": f"Patrón regex inválido: {e}"}]

    # Obtener lista de archivos a procesar
    files_to_search = []

    if include_pattern:
        # Usar el patrón de inclusión
        files_to_search = glob.glob(include_pattern, recursive=True)
    else:
        # Buscar todos los archivos en el directorio actual
        files_to_search = glob.glob("**/*", recursive=True)

    # Filtrar solo archivos (no directorios)
    files_to_search = [f for f in files_to_search if os.path.isfile(f)]

    # Aplicar patrón de exclusión si existe
    if exclude_pattern:
        files_to_search = [f for f in files_to_search if not fnmatch.fnmatch(f, exclude_pattern)]

    # Buscar en cada archivo
    for file_path in files_to_search:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                for line_num, line in enumerate(file, 1):
                    matches = pattern.finditer(line)
                    for match in matches:
                        results.append(
                            {
                                "file": file_path,
                                "line_number": line_num,
                                "line_content": line.rstrip("\n"),
                                "match": match.group(),
                                "start_pos": match.start(),
                                "end_pos": match.end(),
                            }
                        )
        except (IOError, UnicodeDecodeError) as e:
            results.append({"file": file_path, "error": f"Error al leer archivo: {e}"})
    # convert results to a string
    results = ""
    for result in results:
        results += str(result) + "\n"

    return results


async def codebase_search(
    query: str,
    target_directories: Optional[List[str]] = None,
    explanation: str = "",
) -> str:
    """
    Find snippets of code from the codebase most relevant to the search query.
    This is a semantic search tool, so the query should ask for something semantically
    matching what is needed.

    Parameters
    ----------
    query : str
        Search query (should be reused verbatim from user's prompt).
    target_directories : list[str] | None
        Optional list of directories to constrain the search to.
    explanation : str
        One-sentence explanation of why this invocation is being made.

    Returns
    -------
    str
        Human-readable summary of matching files (limited to MAX_RESULTS).
    """
    # Preparar raíces de búsqueda
    roots = [Path(d).expanduser().resolve() for d in (target_directories or ["."])]

    # Compilar patrón (regExp) a partir de la query literal
    flags = 0 if CASE_SENSITIVE else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)

    # 1. Recolectar paths candidatos
    all_files = _iter_code_files(roots, tuple(e.lower() for e in DEFAULT_EXTS))

    # 2. Buscar en paralelo
    matches: list[str] = []
    with cf.ThreadPoolExecutor() as pool:
        for path in pool.map(lambda p: _file_contains(pattern, p), all_files):
            if path:
                matches.append(str(path))
                if len(matches) >= MAX_RESULTS:
                    break

    # 3. Formatear salida
    header = (
        f"Search completed for query: '{query}'. "
        f"{explanation or 'Semantic code search triggered.'}\n"
        f"Results: {len(matches)} file(s) matched.\n"
    )
    body = "\n".join(matches)
    return header + (body or "No relevant files found.")


async def run_terminal_cmd(command: str, require_user_approval: bool = False) -> str:
    """Ejecuta un comando de terminal"""
    dangerous_keywords = [
        "rm",
        "del",
        "format",
        "shutdown",
        "reboot",
        "kill",
        "pip install",
        "npm install",
        "apt-get",
        "yum",
        "curl",
        "wget",
    ]

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
            command, shell=True, capture_output=True, text=True, timeout=60, cwd=WORKSPACE
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
            target = (
                WORKSPACE / target_file
                if not Path(target_file).is_absolute()
                else Path(target_file)
            )
            cmd.extend(["--", str(target)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=WORKSPACE)

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
                diff_cmd, capture_output=True, text=True, timeout=10, cwd=WORKSPACE
            )

            if diff_result.stdout:
                lines = diff_result.stdout.split("\n")[:100]
                output += "\n\nLast change:\n" + "\n".join(lines)
                if len(diff_result.stdout.split("\n")) > 100:
                    output += "\n... (output truncated)"

        return output

    except FileNotFoundError:
        return "Error: git is not installed"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out"
    except Exception as e:
        return f"Error getting diff history: {str(e)}"
