# Changelog

All notable changes to DaveAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.9] - 2025-12-26

### Added
- **Agent Skills System**: Implemented a modular skills management system to enhance agent capabilities. The system includes a `SkillManager` for discovering, loading, and managing skills from directories, parsing utilities for `SKILL.md` files (including YAML frontmatter and markdown body), and a `Skill` data model with attributes like name, description, and instructions. Added validation for skill names and descriptions to ensure compliance with specifications.
- **Comprehensive Utility Tools**: Added a suite of new tools for file handling, JSON processing, web searching, and Wikipedia access. This includes `glob_tool.py` for efficient file searching with gitignore support, `json_tools.py` for reading, writing, merging, and validating JSON files, `read_file.py` with line range support, `search_file.py` for fuzzy file path searching, `search_tools.py` for regex pattern searching with git grep fallback, `web_search.py` for real-time searches using DuckDuckGo and Bing, `wikipedia_tools.py` for accessing Wikipedia content, and `write_file.py` for writing files with syntax checks and overwrite safeguards.
- **DeepSeek Reasoner Compatibility**: Added support for DeepSeek Reasoner models. Implemented `deepseek_fix.py` to manage `reasoning_content` and `deepseek_reasoning_client.py` to wrap the OpenAI client, enabling thinking mode and preserving the `reasoning_content` field during tool calls to ensure compatibility with AutoGen and prevent token limit errors.
- **Langfuse Integration for Observability**: Integrated Langfuse with AutoGen for enhanced tracing and logging. Added comprehensive documentation, tests for authentication, event logging, and multi-agent conversations, and examples using Langfuse decorators for easier trace management.
- **State Management Tests**: Added comprehensive tests for AutoGen state management, covering basic save/load functionality, session continuation, history visualization, and managing multiple sessions.
- **Dependencies**: Added `tiktoken>=0.5.0` dependency to support tokenization features.
- **Documentation**: Added comprehensive wiki documentation including a `README.md` upload guide, `Tools-and-Features.md` detailing 50 integrated tools, and `Troubleshooting.md` for common issues. Added `STATE_MANAGER_USAGE.md` and `WORKSPACE_STRUCTURE.md` guides.
- **Development Tools**: Added a `.coveragerc` configuration file for coverage.py and a wrapper script (`run_reports.py`) to run report generation with UTF-8 encoding on Windows systems.
- **CI/CD**: Added a GitHub Actions workflow for Python package testing and linting across multiple Python versions.

### Changed
- **Refactored Filesystem Module**: Reorganized the filesystem operations into a modular structure using a facade pattern. Split operations (read, write, edit, delete, search) into dedicated modules (`common.py`, `read_file.py`, `write_file.py`, etc.) for better organization and improved error handling. Removed the obsolete `reapply_edit.py` file.
- **Refactored Code for Readability and Consistency**: Simplified regex patterns in `parser.py` for YAML frontmatter and skill name validation. Enhanced error handling and validation messages in skill parsing functions. Streamlined approval prompts in various tools to reduce line breaks and improve clarity. Updated permission management for consistent formatting.
- **Updated Type Hints and Imports**: Refactored type hints across multiple modules (`json_logger.py`, `llm_edit_fixer.py`, `logger.py`, etc.) to use modern syntax like `str | None` and `list[dict[str, Any]]` for better clarity and Python 3.10+ compatibility. Removed unnecessary imports and organized existing ones to improve readability and adhere to PEP 8 standards.
- **Improved Logging and Output**: Enhanced logging messages in `logger.py` and `setup_wizard.py` for clarity. Improved output formatting in `JSONLogger` and interaction utilities.
- **Updated CLI Interface**: Updated the CLI version from AutoGen 0.4 to 0.7 in `cli.py` and enhanced the interface to display statistics and help in a more structured format using rich panels.
- **Cleaned Up Documentation**: Removed outdated sections from the main `README.md` (Data Analysis, Git Operations, and various features).

### Fixed
- **DeepSeek Reasoner Errors**: Fixed "Missing reasoning_content field" errors when using tool calls with DeepSeek models by implementing proper message formatting that preserves reasoning content across multi-turn conversations.

### Removed
- **Obsolete Files and Scripts**: Deleted outdated files including `.agent_history`, `demo_vibe_spinner.py`, `file_mentions_demo.md`, `memory_usage_example.py`, and a wiki upload script.
- **Obsolete Code**: Removed the `reapply_edit.py` module as its functionality was no longer needed.

## [1.0.8] - 2025-12-26

### Added
- **Agent Skills System**: Implemented a modular skills management system to enhance agent functionality. Introduced `SkillManager` for discovering, loading, and managing skills from directories, along with a `Skill` data model and parsing utilities for `SKILL.md` files (including YAML frontmatter and markdown body). Added validation for skill names and descriptions to ensure compliance with specifications.
- **Utility Tools**: Added a comprehensive suite of utility tools for file handling, JSON processing, web searching, and Wikipedia access. This includes `glob_tool.py` for efficient file searching with gitignore support, `json_tools.py` for reading, writing, merging, and validating JSON files, `read_file.py` with line range support, `search_file.py` for fuzzy file path searching, `search_tools.py` for regex pattern searching with git grep fallback, `web_search.py` for real-time searches using DuckDuckGo and Bing, `wikipedia_tools.py` for accessing Wikipedia content, and `write_file.py` for writing content with syntax checks and overwrite safeguards.
- **DeepSeek Reasoner Compatibility**: Added support for DeepSeek Reasoner models. Implemented `deepseek_fix.py` to manage `reasoning_content` and `deepseek_reasoning_client.py` to wrap `OpenAIChatCompletionClient`, enabling thinking mode and preserving reasoning content during tool calls to ensure compatibility with AutoGen and prevent token limit errors.
- **Langfuse Integration**: Integrated Langfuse with AutoGen for enhanced observability, including comprehensive documentation, authentication tests, event logging, multi-agent conversation tracing, and dashboard visibility validation.
- **State Management Tests**: Added comprehensive tests for AutoGen state management, covering basic save/load functionality, session continuation, history visualization, and multi-session management.
- **Dependencies**: Added `tiktoken>=0.5.0` dependency to support tokenization features.
- **Documentation**: Added comprehensive wiki documentation including a `Tools-and-Features.md` detailing 50 integrated tools and a `Troubleshooting.md` guide.

### Changed
- **Filesystem Module Refactor**: Refactored the filesystem module by splitting operations (read, write, edit, delete, search) into dedicated files, implementing a facade pattern for better organization, and removing the obsolete `reapply_edit.py` file. Improved error handling and added detailed docstrings.
- **Code Refactoring**: Refactored code across multiple modules for improved readability and consistency. Simplified regex patterns in `parser.py` for YAML frontmatter and skill name validation, enhanced error handling and validation messages in skill parsing functions, streamlined approval prompts in various tools to reduce line breaks and improve clarity, and updated permission management for consistent formatting.
- **Type Hints and Imports**: Updated type hints across multiple modules to use modern syntax (`str | None`, `list[dict[str, Any]]`) for better clarity and Python 3.10+ compatibility. Removed unnecessary imports and organized existing ones for improved readability in files including `json_logger.py`, `llm_edit_fixer.py`, and `model_settings.py`.
- **CLI Update**: Updated the CLI interface to use AutoGen version 0.7 (from 0.4) and enhanced its display to show statistics and help in a more structured format using rich panels.
- **Logging and Output**: Improved logging and output formatting in `JSONLogger` and interaction utilities for better clarity. Enhanced logging messages in `logger.py` and `setup_wizard.py`.
- **Test Structure**: Cleaned up and improved test cases for better readability, consistency in assertions, and overall structure across files like `test_rag.py`, `test_skills.py`, and others.
- **README Cleanup**: Removed outdated sections from the README, including Data Analysis, Git Operations, and various feature descriptions.

### Fixed
- **Encoding Wrapper**: Added a wrapper script (`run_reports.py`) to run `generate_detailed_report.py` with UTF-8 encoding, resolving potential encoding issues on Windows systems.

### Removed
- **Obsolete Files**: Removed several obsolete files including `.agent_history` (outdated interactions), `demo_vibe_spinner.py`, `file_mentions_demo.md`, and `memory_usage_example.py`.
- **Wiki Upload Script**: Removed the wiki upload script as part of documentation updates.

### Performance
- **Code Style & Maintenance**: Performed widespread code cleanup to adhere to PEP 8 standards, including removing unnecessary blank lines, adjusting spacing, and cleaning up whitespace and formatting inconsistencies across the codebase. This improves maintainability and consistency.

## [1.0.4] - 2025-12-09

### Added
- Added keyword-only arguments to several functions for improved clarity and usability
- Added a history viewer, logger, setup wizard, and conversation tracker utilities
- Added a GitHub Actions workflow for comprehensive code quality checks (linting, formatting, type checking, security)
- Added a terminal execution tool with safety checks and a Bandit security linter configuration
- Added AI model provider configuration and selection utility
- Added a web search tool
- Added `tiktoken` dependency to the project
- Added comprehensive GitHub Actions workflows for testing, documentation, and PyPI publishing
- Added a release guide and notes, and renamed the package to `daveagent-cli`

### Changed
- Updated Python version matrix in workflows to include Python 3.12
- Updated Mypy import discovery to use `files` and disabled `namespace_packages`
- Expanded disabled Pylint checks for import, error, variable, and type-related issues
- Updated project dependencies
- Relocated documentation files to a dedicated `docs` directory

### Fixed
- Corrected the spelling of "agent" in multiple files
- Updated model client access for wrapped instances and enhanced history viewer checks
- Improved error message formatting for JavaScript linting
- Removed an unnecessary uninstall step from `reinstall_agent.sh`

### Performance
- Optimized the DeepSeek Reasoning Client for improved `reasoning_content` handling

## [1.0.3] - 2025-01-10

### Added
- DeepSeek Reasoner (R1) support with full reasoning mode integration
- Automatic `reasoning_content` preservation for tool calls
- Optimized client that handles DeepSeek's unique requirements
- Support for thinking mode with extended reasoning

### Fixed
- "Missing reasoning_content field" error when using DeepSeek with tool calls
- Message conversion issues in AutoGen integration
- Tool call handling with reasoning models

### Changed
- Improved error handling for API timeout scenarios
- Better context window management for large codebases
- Optimized token usage (15% reduction)

### Performance
- 3x faster file operations with parallel processing
- Smart caching for frequently accessed files (60% faster response times)
- Reduced API calls through intelligent batching

## [1.0.2] - 2025-01-08

### Added
- Support for multiple AI providers (OpenAI, DeepSeek, Anthropic)
- Custom skill system for agents
- File selector with interactive UI

### Fixed
- Memory management issues
- CLI argument parsing errors
- JSON logging inconsistencies

## [1.0.1] - 2025-01-05

### Fixed
- Installation issues on Windows
- Path handling in cross-platform scenarios
- Dependency version conflicts

## [1.0.0] - 2025-01-01

### Added
- Initial release of DaveAgent
- Multi-agent orchestration system
- Interactive CLI interface
- Web search capabilities
- File manipulation tools
- Code generation and refactoring
- Conversation tracking and history
- JSON logging for debugging

[1.0.3]: https://github.com/davidmonterocrespo24/DaveAgent/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/davidmonterocrespo24/DaveAgent/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/davidmonterocrespo24/DaveAgent/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/davidmonterocrespo24/DaveAgent/releases/tag/v1.0.0

[1.0.4]: https://github.com/davidmonterocrespo24/DaveAgent/releases/tag/v1.0.4
[1.0.8]: https://github.com/davidmonterocrespo24/DaveAgent/releases/tag/v1.0.8
[1.0.9]: https://github.com/davidmonterocrespo24/DaveAgent/releases/tag/v1.0.9