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

    def exists(self, target_dir: Path | None = None) -> bool:
        """
        Check if a DAVEAGENT.md file already exists in the target directory.
        """
        if target_dir is None:
            target_dir = Path.cwd()
        return (target_dir / self.default_filename).exists()

    def get_target_path(self, target_dir: Path | None = None) -> Path:
        """
        Get the full path where DAVEAGENT.md would be created.
        """
        if target_dir is None:
            target_dir = Path.cwd()
        return target_dir / self.default_filename

    def create_empty(self, target_dir: Path | None = None) -> Path:
        """
        Creates an empty DAVEAGENT.md file (to be populated by the LLM agent).
        Returns the path to the created file.
        """
        if target_dir is None:
            target_dir = Path.cwd()

        target_file = target_dir / self.default_filename
        target_file.write_text("", encoding="utf-8")
        return target_file

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

    def get_init_prompt(self) -> str:
        """
        Returns the prompt that instructs the LLM agent to analyze the project
        and generate a comprehensive DAVEAGENT.md file.

        Inspired by Gemini CLI's /init approach: the agent explores the project
        structure, reads key files, and generates context-aware documentation.
        """
        return """You are an AI agent. Your task is to analyze the current directory and generate a comprehensive DAVEAGENT.md file to be used as instructional context for future interactions with this agent.

**Analysis Process:**

1.  **Initial Exploration:**
    *   Start by listing the files and directories to get a high-level overview of the project structure.
    *   Read the README file (e.g., `README.md`, `README.txt`, `README.rst`) if it exists. This is often the best place to start understanding the project.

2.  **Iterative Deep Dive (up to 10 files):**
    *   Based on your initial findings, select the most important files to understand the project (e.g., configuration files, main source files, documentation, entry points).
    *   Read them. As you learn more, refine your understanding and decide which files to read next. You don't need to decide all files at once — let your discoveries guide your exploration.
    *   Prioritize: package.json, pyproject.toml, setup.py, requirements.txt, Makefile, Dockerfile, docker-compose.yml, tsconfig.json, Cargo.toml, go.mod, pom.xml, build.gradle, and main entry point files.

3.  **Identify Project Type:**
    *   **Code Project:** Look for clues like `package.json`, `requirements.txt`, `pyproject.toml`, `setup.py`, `pom.xml`, `go.mod`, `Cargo.toml`, `build.gradle`, or a `src/` directory. If you find them, this is a software project.
    *   **Non-Code Project:** If you don't find code-related files, this might be a directory for documentation, research papers, notes, or something else entirely.

**DAVEAGENT.md Content Generation:**

**For a Code Project, include these sections:**

*   **# Project Overview:** Write a clear and concise summary of the project's purpose, main technologies, architecture, and key dependencies.
*   **# Building and Running:** Document the key commands for building, running, testing, and linting the project. Infer these from the files you've read (e.g., `scripts` in `package.json`, `Makefile` targets, etc.). If you can't find explicit commands, provide a placeholder with a TODO.
*   **# Project Structure:** Brief description of the main directories and their purposes.
*   **# Development Conventions:** Describe coding styles, testing practices, naming conventions, or contribution guidelines you can infer from the codebase (linters, formatters, type checkers, etc.).
*   **# Important Notes:** Any critical information the agent should know — environment variables, external services, deployment patterns, etc.

**For a Non-Code Project, include these sections:**

*   **# Directory Overview:** Describe the purpose and contents of the directory. What is it for? What kind of information does it hold?
*   **# Key Files:** List the most important files and briefly explain what they contain.
*   **# Usage:** Explain how the contents of this directory are intended to be used.

**Final Output:**

Write the complete, well-formatted Markdown content to the `DAVEAGENT.md` file using the write_file tool. The content must be accurate, based on what you actually found in the project — do NOT invent or assume information that isn't there."""
