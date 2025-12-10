# Changelog

All notable changes to DaveAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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