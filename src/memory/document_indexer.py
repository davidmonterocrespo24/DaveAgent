"""
Document Indexer - Index codebase files into memory
"""
import asyncio
import logging
import re
from autogen_core.memory import Memory, MemoryContent, MemoryMimeType
from pathlib import Path
from typing import List, Optional, Dict, Any


class DocumentIndexer:
    """
    Document indexer for codebase files

    Walks through the project directory, chunks code files,
    and stores them in vector memory for retrieval.
    """

    def __init__(
            self,
            memory: Memory,
            chunk_size: int = 1500,
            ignore_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the document indexer

        Args:
            memory: Memory store to add indexed documents to
            chunk_size: Maximum characters per chunk
            ignore_patterns: Patterns to ignore (e.g., node_modules, .git)
        """
        self.memory = memory
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

        # Default ignore patterns
        self.ignore_patterns = ignore_patterns or [
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            ".env",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            "*.pyo",
            "*.egg-info",
            ".daveagent",  # Don't index our own data
        ]

        # Supported file extensions
        self.supported_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".java", ".cpp", ".c", ".cs", ".go",
            ".rs", ".rb", ".php", ".swift", ".kt",
            ".scala", ".html", ".css", ".scss",
            ".json", ".yaml", ".yml", ".toml",
            ".md", ".txt", ".sh", ".bash"
        }

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored"""
        path_str = str(path)

        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                # Wildcard pattern
                if path_str.endswith(pattern[1:]):
                    return True
            else:
                # Directory or file name pattern
                if pattern in path_str:
                    return True

        return False

    def _is_supported_file(self, path: Path) -> bool:
        """Check if a file is supported for indexing"""
        return path.suffix.lower() in self.supported_extensions

    def _extract_functions_and_classes(self, code: str, language: str) -> Dict[str, Any]:
        """
        Extract function and class definitions from code

        Args:
            code: Source code content
            language: Programming language

        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "functions": [],
            "classes": []
        }

        try:
            if language == "python":
                # Extract Python functions
                func_pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
                functions = re.findall(func_pattern, code)
                metadata["functions"] = functions

                # Extract Python classes
                class_pattern = r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]"
                classes = re.findall(class_pattern, code)
                metadata["classes"] = classes

            elif language in ["javascript", "typescript"]:
                # Extract JS/TS functions
                func_pattern = r"(?:function\s+|const\s+|let\s+|var\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=\s*)?(?:async\s*)?\([^)]*\)\s*(?:=>|{)"
                functions = re.findall(func_pattern, code)
                metadata["functions"] = functions

                # Extract JS/TS classes
                class_pattern = r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)"
                classes = re.findall(class_pattern, code)
                metadata["classes"] = classes

        except Exception as e:
            self.logger.warning(f"Failed to extract functions/classes: {e}")

        return metadata

    def _chunk_code(self, code: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        """
        Split code into chunks with metadata

        Args:
            code: Source code content
            file_path: Path to the source file
            language: Programming language

        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []

        # Try to split by logical sections first (functions, classes)
        if language == "python":
            # Split by top-level definitions
            pattern = r"(?=^(?:def|class|async def)\s)"
            sections = re.split(pattern, code, flags=re.MULTILINE)
        else:
            # For other languages, just split by size
            sections = [code]

        current_chunk = ""
        chunk_index = 0

        for section in sections:
            if not section.strip():
                continue

            # If section fits in remaining chunk space, add it
            if len(current_chunk) + len(section) < self.chunk_size:
                current_chunk += section
            else:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "chunk_index": chunk_index,
                        "file_path": file_path,
                        "language": language
                    })
                    chunk_index += 1

                # Start new chunk with current section
                current_chunk = section

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "file_path": file_path,
                "language": language
            })

        return chunks

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sh": "bash",
            ".bash": "bash",
        }
        return language_map.get(ext, "text")

    async def index_file(self, file_path: Path, project_root: Optional[Path] = None) -> int:
        """
        Index a single file into memory

        Args:
            file_path: Path to the file to index
            project_root: Root directory of the project (for relative paths)

        Returns:
            Number of chunks indexed
        """
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Get relative path if project_root provided
            if project_root:
                try:
                    relative_path = str(file_path.relative_to(project_root))
                except ValueError:
                    relative_path = str(file_path)
            else:
                relative_path = str(file_path)

            # Detect language
            language = self._detect_language(file_path)

            # Extract metadata
            metadata_extra = self._extract_functions_and_classes(content, language)

            # Chunk the code
            chunks = self._chunk_code(content, relative_path, language)

            # Add each chunk to memory
            for chunk_data in chunks:
                chunk_metadata = {
                    "file_path": chunk_data["file_path"],
                    "language": chunk_data["language"],
                    "chunk_index": chunk_data["chunk_index"],
                    "total_chunks": len(chunks),
                    "type": "code",
                }

                # Add function/class info to first chunk
                if chunk_data["chunk_index"] == 0:
                    # ChromaDB doesn't support lists in metadata, so we join them
                    flat_metadata = {}
                    for key, value in metadata_extra.items():
                        if isinstance(value, list):
                            flat_metadata[key] = ", ".join(str(v) for v in value)
                        else:
                            flat_metadata[key] = value

                    chunk_metadata.update(flat_metadata)

                await self.memory.add(
                    MemoryContent(
                        content=chunk_data["content"],
                        mime_type=MemoryMimeType.TEXT,
                        metadata=chunk_metadata
                    )
                )

            self.logger.debug(f"✓ Indexed {file_path.name}: {len(chunks)} chunks")
            return len(chunks)

        except Exception as e:
            self.logger.error(f"Failed to index {file_path}: {e}")
            return 0

    async def index_directory(
            self,
            directory: Path,
            recursive: bool = True,
            max_files: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Index all supported files in a directory

        Args:
            directory: Directory to index
            recursive: Whether to index subdirectories
            max_files: Maximum number of files to index (None for unlimited)

        Returns:
            Dictionary with indexing statistics
        """
        stats = {
            "files_indexed": 0,
            "files_skipped": 0,
            "chunks_created": 0,
            "errors": 0
        }

        try:
            # Get list of files to index
            if recursive:
                files = list(directory.rglob("*"))
            else:
                files = list(directory.glob("*"))

            # Filter to supported files and respect ignore patterns
            files_to_index = [
                f for f in files
                if f.is_file()
                   and self._is_supported_file(f)
                   and not self._should_ignore(f)
            ]

            # Limit number of files if specified
            if max_files:
                files_to_index = files_to_index[:max_files]

            self.logger.info(f"📚 Indexing {len(files_to_index)} files from {directory}")

            # Index files
            for file_path in files_to_index:
                try:
                    chunks = await self.index_file(file_path, project_root=directory)
                    if chunks > 0:
                        stats["files_indexed"] += 1
                        stats["chunks_created"] += chunks
                    else:
                        stats["files_skipped"] += 1

                except Exception as e:
                    self.logger.error(f"Error indexing {file_path}: {e}")
                    stats["errors"] += 1

            self.logger.info(
                f"✅ Indexing complete: {stats['files_indexed']} files, "
                f"{stats['chunks_created']} chunks"
            )

        except Exception as e:
            self.logger.error(f"Failed to index directory {directory}: {e}")
            stats["errors"] += 1

        return stats

    async def index_project(
            self,
            project_dir: Optional[Path] = None,
            max_files: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Index the entire project directory

        Args:
            project_dir: Project directory (defaults to current directory)
            max_files: Maximum number of files to index

        Returns:
            Dictionary with indexing statistics
        """
        if project_dir is None:
            project_dir = Path.cwd()

        self.logger.info(f"🚀 Starting project indexing: {project_dir}")

        stats = await self.index_directory(
            directory=project_dir,
            recursive=True,
            max_files=max_files
        )

        return stats
