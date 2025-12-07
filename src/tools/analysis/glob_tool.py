import os
import glob
import time
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from src.tools.filesystem.common import get_workspace

# Configure logging
logger = logging.getLogger(__name__)

RECENCY_THRESHOLD_SECONDS = 24 * 60 * 60  # 24 hours


# Intentar importar pathspec para manejo robusto de .gitignore
import pathspec

WORKSPACE = Path(os.getcwd()).resolve()

def _load_gitignore_patterns(root_path: Path) -> Optional['pathspec.PathSpec']:
    gitignore = root_path / ".gitignore"
    if gitignore.exists():
        with open(gitignore, "r") as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f)
    return None

def _is_ignored(path: Path, spec: Optional['pathspec.PathSpec']) -> bool:
    # Exclusiones hardcoded de seguridad
    if ".git" in path.parts: return True
    if "node_modules" in path.parts: return True
    if "__pycache__" in path.parts: return True
    
    if spec:
        # pathspec espera rutas relativas
        try:
            rel_path = path.relative_to(WORKSPACE)
            return spec.match_file(str(rel_path))
        except ValueError:
            return False
    return False

def _sort_file_entries(entries: List[Path]) -> List[Path]:
    """
    Sorts file entries based on recency and then alphabetically.
    Recent files (modified within 24h) are listed first, newest to oldest.
    Older files are listed after recent ones, sorted alphabetically by path.
    """
    now = time.time()
    
    def get_sort_key(path_obj: Path):
        try:
            stat = path_obj.stat()
            mtime = stat.st_mtime
        except Exception:
            mtime = 0
            
        is_recent = (now - mtime) < RECENCY_THRESHOLD_SECONDS
        
        # Key tuple: (is_old_bool, neg_mtime_if_recent, path_str)
        # is_recent = True => we want it first.
        # So is_old = False (0).
        
        if is_recent:
            # Recent files: Sort by mtime descending (newest first)
            return (0, -mtime, str(path_obj))
        else:
            # Older files: Sort by path ascending
            return (1, 0, str(path_obj))

    return sorted(entries, key=get_sort_key)

async def glob_search(
    pattern: str,
    dir_path: Optional[str] = None,
    case_sensitive: bool = False,
    respect_git_ignore: bool = True,
    respect_gemini_ignore: bool = True
) -> str:
    """
    Efficiently finds files matching specific glob patterns.
    
    Args:
        pattern: The glob pattern to match files against (e.g. '**/*.py').
        dir_path: Optional directory to search in. Defaults to workspace root.
        case_sensitive: Whether search should be case sensitive (OS dependent in Python).
        respect_git_ignore: Whether to exclude files ignored by git.
        respect_gemini_ignore: Placeholder for gemini ignore (not implemented).
    """
    try:
        workspace = get_workspace()
        
        # Determine search directory
        if dir_path:
            search_dir = Path(dir_path)
            if not search_dir.is_absolute():
                search_dir = workspace / search_dir
        else:
            search_dir = workspace
            
        if not search_dir.exists():
            return f"Error: Search path does not exist: {search_dir}"
            
        # Construct absolute pattern for glob
        # Note: glob.glob with recursive=True requires the pattern to contain '**' for directory recursion
        # If the user provided 'src/*.ts', it's not recursive.
        # If they provided '**/*.ts', it is.
        
        # We need to handle the pattern carefully.
        # If pattern is absolute, use it.
        # If relative, join with search_dir.
        
        if Path(pattern).is_absolute():
            full_pattern = pattern
        else:
            full_pattern = str(search_dir / pattern)
        gitignore_spec = _load_gitignore_patterns(workspace) if respect_git_ignore else None    
        # Execute glob
        # recursive=True allows '**' to match directories
        files = glob.glob(full_pattern, recursive=True)
        
        # Filter for files only (glob returns dirs too sometimes)
        path_entries = []
        for f in files:
            p = Path(f)
            if p.is_file():
                path_entries.append(p)
                
        # Filter ignored files
        if respect_git_ignore:
            # We filter out files that are git ignored
            # This can be slow for many files.
            # Optimization: Only check if we are in a git repo.
            if (workspace / ".git").exists():
                filtered = []
                for p in path_entries:
                    if not _is_ignored(p, gitignore_spec):
                        filtered.append(p)
                path_entries = filtered
                
        if not path_entries:
            return f"No files found matching pattern \"{pattern}\" within {search_dir}"
            
        # Sort
        sorted_entries = _sort_file_entries(path_entries)
        
        # Format output
        count = len(sorted_entries)
        
        # We return absolute paths as per TS description ("returning absolute paths")
        file_list = "\n".join([str(p) for p in sorted_entries])
        
        return f"Found {count} file(s) matching \"{pattern}\" within {search_dir}, sorted by modification time (newest first):\n{file_list}"

    except Exception as e:
        return f"Error during glob search operation: {str(e)}"
