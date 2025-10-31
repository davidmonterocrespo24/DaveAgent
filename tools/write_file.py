import os
from typing import Union
from pathlib import Path

# Importa el decorador de herramientas desde el ADK de watsonx Orchestrate
from ibm_watsonx_orchestrate.agent_builder.tools import tool

WORKSPACE = Path(r"/home/testagent/workspace").resolve()

# Validación: la carpeta debe existir
WORKSPACE.mkdir(parents=True, exist_ok=True)

# Cambiar cwd *una sola vez* para todo el proceso
os.chdir(WORKSPACE)
print(f"[Init] Current working dir set to {os.getcwd()}")

def to_workspace_path(path_like: Union[str, Path]) -> Path:
    """
    Devuelve la ruta ABSOLUTA dentro del WORKSPACE.
    • Si el path es relativo → WORKSPACE / path
    • Si es absoluto y ya está dentro del WORKSPACE → se devuelve tal cual
    • Si es absoluto y sale del WORKSPACE → ValueError
    """
    p = Path(path_like)
    if not p.is_absolute():
        p = WORKSPACE / p
    p = p.resolve()

    if WORKSPACE not in p.parents and p != WORKSPACE:
        raise ValueError(f"Ruta fuera del workspace: {p}")
    return p


@tool
def write_file(file_path: str, content: str, explanation: str = "") -> str:
    """
    Write content to a file in the workspace, creating directories if necessary.
    
    Parameters:
        file_path (str): Path to the file to be created or overwritten
        content (str): Content to write to the file
    
    Returns:
        str: Success message with file path or error message if operation failed
    """
    try:
        abs_path = to_workspace_path(file_path)        # <<<<<<
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        return f"Archivo guardado en {abs_path}"
    except Exception as e:
        return f"Error escribiendo archivo: {e}"