import re
import glob
import os
import fnmatch

# Importa el decorador de herramientas desde el ADK de watsonx Orchestrate
from ibm_watsonx_orchestrate.agent_builder.tools import tool

@tool
def grep_search(query, case_sensitive=True, include_pattern=None, exclude_pattern=None, explanation=None):
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
        files_to_search = [f for f in files_to_search 
                          if not fnmatch.fnmatch(f, exclude_pattern)]
    
    # Buscar en cada archivo
    for file_path in files_to_search:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    matches = pattern.finditer(line)
                    for match in matches:
                        results.append({
                            "file": file_path,
                            "line_number": line_num,
                            "line_content": line.rstrip('\n'),
                            "match": match.group(),
                            "start_pos": match.start(),
                            "end_pos": match.end()
                        })
        except (IOError, UnicodeDecodeError) as e:
            results.append({
                "file": file_path,
                "error": f"Error al leer archivo: {e}"
            })
    
    return results
