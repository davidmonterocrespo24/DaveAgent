import os
from typing import List, Tuple, Union
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
def list_dir(relative_workspace_path: str, explanation: str = "") -> str:
    """
    List the contents of a directory recursively, showing all files and subdirectories.
    
    Parameters:
        relative_workspace_path (str): The relative path to the directory within the workspace
        explanation (str): Optional explanation for the directory listing operation
    
    Returns:
        str: Complete directory structure with files and folders, including file sizes and summary statistics
    """
    
    try:
        path = to_workspace_path(relative_workspace_path)
        if not path.exists():
            return f"Directory '{relative_workspace_path}' does not exist"
        
        def _get_all_items(current_path: Path, relative_to: Path) -> List[Tuple[str, bool, int]]:
            """Obtiene todos los elementos recursivamente"""
            items = []
            
            try:
                for item in current_path.rglob("*"):
                    if item.is_file():
                        try:
                            size = item.stat().st_size
                            rel_path = item.relative_to(relative_to)
                            items.append((str(rel_path), False, size))
                        except (OSError, PermissionError):
                            rel_path = item.relative_to(relative_to)
                            items.append((str(rel_path), False, -1))
                    elif item.is_dir() and not item.name.startswith('.'):
                        rel_path = item.relative_to(relative_to)
                        items.append((str(rel_path), True, 0))
            except Exception:
                pass
                
            return sorted(items, key=lambda x: x[0].lower())
        
        all_items = _get_all_items(path, path)
        
        result_lines = [f"Complete contents of '{relative_workspace_path}':"]
        
        for item_path, is_dir, size in all_items:
            if is_dir:
                result_lines.append(f"📁 {item_path}/")
            else:
                if size >= 0:
                    result_lines.append(f"📄 {item_path} ({size} bytes)")
                else:
                    result_lines.append(f"📄 {item_path} (size unknown)")
        
        dir_count = sum(1 for _, is_dir, _ in all_items if is_dir)
        file_count = sum(1 for _, is_dir, _ in all_items if not is_dir)
        
        result_lines.append(f"\nSummary: {dir_count} directories, {file_count} files")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Error listing directory: {str(e)}"
