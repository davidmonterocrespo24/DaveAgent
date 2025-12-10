# Changelog

All notable changes to DaveAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
