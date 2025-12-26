"""
File Indexer - Indexes all files in the directory for @ mentions
"""

import os
from pathlib import Path


class FileIndexer:
    """Indexes files in the current directory for quick lookup"""

    def __init__(self, root_dir: str = "."):
        """
        Initialize the file indexer

        Args:
            root_dir: Root directory to index (default: current directory)
        """
        self.root_dir = Path(root_dir).resolve()
        self.indexed_files: list[str] = []
        self.excluded_patterns: set[str] = {
            # Directories to exclude
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            "egg-info",
            ".idea",
            "logs",
            # File patterns to exclude (handled by hidden file check)
        }

    def should_exclude_path(self, path: Path) -> bool:
        """
        Check if a path should be excluded from indexing

        Args:
            path: Path to check

        Returns:
            True if path should be excluded
        """
        # Exclude hidden files/directories (starting with .)
        if any(part.startswith(".") for part in path.parts):
            return True

        # Exclude specific directory names
        if any(excluded in path.parts for excluded in self.excluded_patterns):
            return True

        # Exclude binary files and large files
        if path.is_file():
            # Check file extension
            excluded_extensions = {
                ".pyc",
                ".pyo",
                ".so",
                ".dll",
                ".dylib",
                ".exe",
                ".bin",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".pdf",
                ".zip",
                ".tar",
                ".gz",
                ".rar",
                ".mp3",
                ".mp4",
                ".avi",
                ".mov",
            }
            if path.suffix.lower() in excluded_extensions:
                return True

        return False

    def index_directory(self) -> list[str]:
        """
        Index all files in the directory tree

        Returns:
            List of relative file paths
        """
        self.indexed_files = []

        try:
            for root, dirs, files in os.walk(self.root_dir):
                root_path = Path(root)

                # Filter out excluded directories (modifies dirs in-place)
                dirs[:] = [d for d in dirs if not self.should_exclude_path(root_path / d)]

                # Add files to index
                for file in files:
                    file_path = root_path / file

                    if self.should_exclude_path(file_path):
                        continue

                    # Get relative path from root_dir
                    try:
                        relative_path = file_path.relative_to(self.root_dir)
                        # Convert to forward slashes for consistency
                        path_str = str(relative_path).replace("\\", "/")
                        self.indexed_files.append(path_str)
                    except ValueError:
                        # Path is not relative to root_dir
                        continue

            # Sort for better UX
            self.indexed_files.sort()

        except Exception as e:
            print(f"Error indexing directory: {e}")

        return self.indexed_files

    def search_files(self, query: str) -> list[str]:
        """
        Search for files matching a query

        Args:
            query: Search query (can be partial path or filename)

        Returns:
            List of matching file paths
        """
        if not query:
            return self.indexed_files

        query_lower = query.lower()
        matches = []

        for file_path in self.indexed_files:
            # Match if query is in the path
            if query_lower in file_path.lower():
                matches.append(file_path)

        return matches

    def get_file_count(self) -> int:
        """Get total number of indexed files"""
        return len(self.indexed_files)

    def get_absolute_path(self, relative_path: str) -> str:
        """
        Convert relative path to absolute path

        Args:
            relative_path: Relative file path

        Returns:
            Absolute file path
        """
        return str(self.root_dir / relative_path)
