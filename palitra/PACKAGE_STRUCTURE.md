# Palitra Package Structure

The palitra library is organized into logical packages for better maintainability and clarity.

## Overview

```
palitra/
├── __init__.py          # Main public interface
├── __init__.pyi         # Type stubs for main interface
├── core/                # Core functionality
│   ├── __init__.py
│   ├── runner.py        # EventLoopThreadRunner class
│   ├── runner.pyi       # Type stubs for runner
│   └── README.md        # Documentation for core package
├── utils/               # Utility modules
│   ├── __init__.py
│   ├── exceptions.py    # Custom exception classes
│   ├── exceptions.pyi   # Type stubs for exceptions
│   ├── logging.py       # Logging configuration
│   ├── logging.pyi      # Type stubs for logging
│   └── README.md        # Documentation for utils package
└── api/                 # High-level API
    ├── __init__.py
    ├── singleton.py     # Global singleton and convenience functions
    ├── singleton.pyi    # Type stubs for singleton
    └── README.md        # Documentation for api package
```

## Package Responsibilities

### Core Package (`palitra.core`)
Contains the main `EventLoopThreadRunner` class and related core functionality:
- Event loop management in background threads
- Thread-safe coroutine execution
- Context manager support
- Resource cleanup and shutdown

### Utils Package (`palitra.utils`)
Contains utility modules used throughout the library:
- Custom exception classes (`PalitraError`, `DeadlockError`, `RunnerError`)
- Logging configuration with Loguru
- Environment-based configuration

### API Package (`palitra.api`)
Provides high-level convenience functions:
- Global singleton runner management
- `run()` function for single coroutine execution
- `gather()` function for concurrent execution
- `shutdown_global_runner()` for cleanup
- `is_runner_alive()` for status checking

## Import Patterns

### Public API (Recommended)
```python
from palitra import run, gather, EventLoopThreadRunner
```

### Direct Package Access
```python
from palitra.core import EventLoopThreadRunner
from palitra.utils import logger, PalitraError
from palitra.api import run, gather
```

### Individual Module Access
```python
from palitra.core.runner import EventLoopThreadRunner
from palitra.utils.exceptions import DeadlockError
from palitra.api.singleton import shutdown_global_runner
```

## Benefits of This Structure

1. **Separation of Concerns**: Each package has a clear responsibility
2. **Maintainability**: Easier to locate and modify specific functionality
3. **Type Safety**: Dedicated .pyi files for each module
4. **Documentation**: Each package has its own README
5. **Extensibility**: Easy to add new packages or modules
6. **Import Clarity**: Clear import paths indicate functionality

## Migration from Flat Structure

The public API remains unchanged, so existing code continues to work:

```python
# Old way (still works)
from palitra import run, gather

# New way (same result)
from palitra import run, gather
```

## Development Guidelines

- Keep core functionality in the `core` package
- Put utilities and helpers in the `utils` package
- Place high-level APIs in the `api` package
- Always include corresponding .pyi files for type safety
- Update package READMEs when adding new functionality
- Maintain backward compatibility in the main `__init__.py` 