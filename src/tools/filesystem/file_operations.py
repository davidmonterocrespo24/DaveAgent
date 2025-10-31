"""
Operaciones de sistema de archivos - Consolidado
"""
import os
from pathlib import Path

WORKSPACE = Path(os.getcwd()).resolve()


async def read_file(target_file: str, start_line_one_indexed: int = 1, max_lines: int = 2000) -> str:
    """
    Lee el contenido de un archivo.

    Args:
        target_file: Ruta al archivo
        start_line_one_indexed: Línea inicial (1-indexed)
        max_lines: Máximo de líneas a leer

    Returns:
        Contenido del archivo con números de línea
    """
    try:
        target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)

        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_idx = max(0, start_line_one_indexed - 1)
        end_idx = min(len(lines), start_idx + max_lines)

        result = f"File: {target} (lines {start_line_one_indexed}-{start_idx + len(lines[start_idx:end_idx])})\n"
        for i, line in enumerate(lines[start_idx:end_idx], start=start_line_one_indexed):
            result += f"{i:4d} | {line.rstrip()}\n"

        if end_idx < len(lines):
            result += f"\n... (truncated, {len(lines) - end_idx} more lines)"

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


async def edit_file(
    target_file: str,
    start_line_one_indexed: int,
    end_line_one_indexed_inclusive: int,
    new_content: str
) -> str:
    """Edita un archivo reemplazando líneas"""
    try:
        target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)

        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_idx = max(0, start_line_one_indexed - 1)
        end_idx = min(len(lines), end_line_one_indexed_inclusive)

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


async def delete_file(target_file: str) -> str:
    """Elimina un archivo"""
    try:
        target = WORKSPACE / target_file if not Path(target_file).is_absolute() else Path(target_file)
        target.unlink()
        return f"Successfully deleted {target}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


async def file_search(query: str) -> str:
    """Busca archivos por nombre"""
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
