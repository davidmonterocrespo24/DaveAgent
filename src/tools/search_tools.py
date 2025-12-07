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
import shutil
from src.tools.common import get_workspace

WORKSPACE = Path(os.getcwd()).resolve()

# --- Configuración de Exclusiones (Fallback) ---
# Se usa solo si git grep no está disponible
EXCLUDED_DIRS = {
    'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env', 
    '.pytest_cache', '.mypy_cache', '.tox', 'dist', 'build', 
    'site-packages', '.next', '.nuxt', 'coverage', '.idea', '.vscode'
}

EXCLUDED_EXTS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin', '.obj', '.o',
    '.min.js', '.min.css', '.map', '.lock', '.log', '.sqlite', '.db',
    '.jpg', '.jpeg', '.png', '.gif', '.ico', '.pdf', '.woff', '.ttf'
}

# --- Helper Functions ---

def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()

def _run_git_grep(query: str, path: Path, include: Optional[str] = None, case_sensitive: bool = False) -> str | None:
    """Ejecuta 'git grep' optimizado."""
    if not shutil.which("git"):
        return None
        
    cmd = ["git", "grep", "-n", "-I"] # -n: line numbers, -I: ignore binary
    
    if not case_sensitive:
        cmd.append("-i")
        
    # Extended regex para mayor compatibilidad
    cmd.append("-E") 
    
    # Construir comando
    # Nota: git grep maneja includes al final con --
    cmd.append(query)
    
    if include:
        cmd.append("--")
        cmd.append(include)
        
    try:
        # Ejecutar en el directorio objetivo
        result = subprocess.run(
            cmd, 
            cwd=str(path),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            return result.stdout
        elif result.returncode == 1:
            return "" # No matches found
        else:
            return None # Error en ejecución (ej. bad regex)
            
    except Exception:
        return None

def _python_grep_fallback(query: str, root_path: Path, include_pattern: str | None, case_sensitive: bool) -> str:
    """Implementación pura en Python (lenta pero segura)."""
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE
    
    try:
        pattern = re.compile(query, flags)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    # Recolectar archivos
    # Si hay include_pattern, usamos glob con ese patrón, si no rglob('*')
    search_pattern = include_pattern if include_pattern else "**/*"
    
    # Manejo básico de glob relativo si el include no tiene **
    if include_pattern and not include_pattern.startswith("**"):
         # Si el usuario pide "*.py", queremos buscar recursivamente "**/*.py"
         # Esto es una heurística común para UX de grep
         pass 

    try:
        # Usamos rglob para iterar eficientemente
        # Nota: Path.rglob no acepta patterns complejos como exclude, hay que filtrar manual
        files_iter = root_path.rglob(search_pattern) if include_pattern else root_path.rglob("*")
        
        for file_path in files_iter:
            if not file_path.is_file():
                continue
                
            # Filtros de exclusión
            if any(part in EXCLUDED_DIRS for part in file_path.parts):
                continue
            if file_path.suffix.lower() in EXCLUDED_EXTS:
                continue
                
            try:
                # Lectura línea a línea para no cargar archivos grandes en memoria
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            # Formato compatible con git grep: file:line:content
                            # Truncamos líneas muy largas para no saturar contexto
                            clean_line = line.strip()[:300] 
                            rel_path = file_path.relative_to(root_path)
                            results.append(f"{rel_path}:{i}:{clean_line}")
                            
                            if len(results) >= 1000: # Safety break
                                results.append("... (too many matches, truncated)")
                                return "\n".join(results)
                                
            except Exception:
                continue
                
    except Exception as e:
        return f"Error in python grep: {e}"

    return "\n".join(results)

# --- Main Tool ---

async def grep_search(
    query: str,
    case_sensitive: bool = False,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None, # Deprecated in favor of gitignore but kept for compat
    explanation: Optional[str] = None
) -> str:
    """
    Search for a regex pattern in files.
    """
    workspace = get_workspace()
    
    # 1. Intentar Git Grep (Estrategia Rápida)
    # Solo si estamos en un repo git y no hay patrones de exclusión complejos 
    # (git grep usa .gitignore, que suele ser lo que queremos)
    if _is_git_repo(workspace) and not exclude_pattern:
        git_output = _run_git_grep(query, workspace, include_pattern, case_sensitive)
        if git_output is not None:
            if not git_output.strip():
                return f"No matches found for '{query}'"
            
            # Limitar salida si es muy larga
            lines = git_output.splitlines()
            if len(lines) > 500:
                return "\n".join(lines[:500]) + f"\n... ({len(lines)-500} more matches truncated)"
            return git_output

    # 2. Fallback a Python (Estrategia Lenta pero Universal)
    # Se usa si falla git grep, si no es repo git, o si hay excludes manuales
    return _python_grep_fallback(query, workspace, include_pattern, case_sensitive)





async def run_terminal_cmd(
    command: str,
    is_background: bool = False,
    require_user_approval: bool = False,
    explanation: str = ""
) -> str:
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



