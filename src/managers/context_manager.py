"""
Manager for DAVEAGENT.md context files.
Handles discovery, reading, and template generation for project-specific context.
"""

from pathlib import Path

from src.utils import get_logger


class ContextManager:
    """
    Manages DAVEAGENT.md files to inject context into the agent.
    Search locations:
    1. Current directory (and parents)
    2. Home directory (~/.daveagent/DAVEAGENT.md)
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.home_context_path = Path.home() / ".daveagent" / "DAVEAGENT.md"
        self.default_filename = "DAVEAGENT.md"

    def discover_context_files(self) -> list[Path]:
        """
        Finds all relevant DAVEAGENT.md files.
        Returns a list of paths from general (home) to specific (closest to current dir).
        """
        found_files: list[Path] = []

        # 1. Home directory context (General)
        if self.home_context_path.exists():
            found_files.append(self.home_context_path)

        # 2. Parent directories (from root to current)
        # Scan from logical root to current working directory
        try:
            cwd = Path.cwd().resolve()
            # We want to find context files in parents, but ordered from top to bottom
            # so that specific overrides general.

            # Get all parents + current dir
            # parents list is [parent(N), ..., parent(0)], so reverse it to get top-down
            search_paths = list(reversed(cwd.parents)) + [cwd]

            for path in search_paths:
                context_file = path / self.default_filename
                if context_file.exists():
                    # Avoid duplicates if home dir is in the path
                    if context_file not in found_files:
                        found_files.append(context_file)

        except Exception as e:
            self.logger.warning(f"Error discovering context files: {e}")

        return found_files

    def get_combined_context(self) -> str:
        """
        Reads and combines all discovered context files.
        Returns the combined context string or empty string.
        """
        files = self.discover_context_files()
        if not files:
            return ""

        context_parts = []
        context_parts.append("\n\n<project_context>")
        context_parts.append(
            "The following context is automatically loaded from DAVEAGENT.md files:\n"
        )

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8")
                context_parts.append(f"--- SOURCE: {file_path} ---")
                context_parts.append(content)
                context_parts.append("\n")
            except Exception as e:
                self.logger.error(f"Failed to read context file {file_path}: {e}")

        context_parts.append("</project_context>\n\n")

        return "\n".join(context_parts)

    def create_template(self, target_dir: Path | None = None) -> Path:
        """
        Creates a DAVEAGENT.md template in the target directory (defaults to cwd).
        """
        if target_dir is None:
            target_dir = Path.cwd()

        target_file = target_dir / self.default_filename

        if target_file.exists():
            raise FileExistsError(f"{self.default_filename} already exists in {target_dir}")

        template_content = """# DAVEAGENT.md - Project Configuration
# This file is automatically loaded into the agent's context.

# Commands
# Define common commands for this project
- npm run build: Build the project
- npm run test: Run tests

# Code Style
# Define coding standards and preferences
- Use descriptive variable names
- Prefer functional components over classes (if React)
- Use type hints in Python

# Workflow & Guidelines
# Important rules for valid changes
- Check for existing utility functions before writing new ones
- Run linters before committing
- Update documentation when changing APIs

# Context
# Any other information the agent should know about this specific project
"""
        target_file.write_text(template_content, encoding="utf-8")
        return target_file
