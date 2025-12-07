"""
Operaciones de sistema de archivos - Consolidado (Facade)
This file now acts as a facade for the specialized modules.
"""
from src.tools.filesystem.common import get_workspace
from src.tools.filesystem.read_file import read_file
from src.tools.filesystem.write_file import write_file
from src.tools.filesystem.edit_file import edit_file
from src.tools.filesystem.directory_ops import list_dir
from src.tools.filesystem.delete_file import delete_file
from src.tools.filesystem.search_file import file_search

__all__ = [
    "get_workspace",
    "read_file",
    "write_file",
    "edit_file",
    "list_dir",
    "delete_file",
    "file_search"
]
