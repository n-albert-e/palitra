# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Performance analysis script
- CLI interface for testing and demos
- Comprehensive documentation and examples
- Package structure with core, utils, and api modules
- Type stub files (.pyi) for better IDE support

### Changed
- Refactored code into logical packages
- Improved error handling and logging
- Enhanced documentation and examples

## [0.1.0] - 2024-12-22

### Added
- Initial release of Palitra library
- `EventLoopThreadRunner` class for managing background event loops
- `run()` function for executing single coroutines from sync context
- `gather()` function for concurrent execution of multiple coroutines
- Global singleton runner with automatic lifecycle management
- Context manager support for automatic cleanup
- Thread-safe operations with deadlock detection
- Comprehensive error handling with custom exceptions
- Logging integration with Loguru
- Optional uvloop support for enhanced performance
- Timeout support for all operations
- Type hints and annotations throughout the codebase

### Features
- **Core Functionality**: Persistent background event loop in dedicated thread
- **Thread Safety**: Safe execution from any thread with deadlock prevention
- **Resource Management**: Automatic cleanup and resource management
- **Performance**: Optional uvloop integration for faster event loops
- **Error Handling**: Comprehensive exception handling with custom error types
- **Logging**: Structured logging with environment-based configuration
- **Type Safety**: Full type annotations and stub files

### Technical Details
- Python 3.8+ support
- MIT License
- No external dependencies (except loguru for logging)
- Optional uvloop for performance enhancement
- Comprehensive test suite
- Full documentation with examples

## [0.0.1] - 2024-12-22

### Added
- Initial development version
- Basic async-to-sync bridge functionality
- Event loop management in background threads 