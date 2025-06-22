# Utils Package

This package contains utility modules for the palitra library.

## Contents

- **`exceptions.py`**: Custom exception classes used throughout the library
- **`logging.py`**: Logging configuration using Loguru
- **`exceptions.pyi`**: Type stub file for exceptions
- **`logging.pyi`**: Type stub file for logging

## Exceptions

### PalitraError
Base exception class for all palitra-specific errors.

### DeadlockError
Raised when an operation would cause a deadlock, typically when `run()` is called from within the runner's own event loop thread.

### RunnerError
Raised for general errors related to the runner's state, such as attempting operations on a closed runner.

## Logging

The logging module configures Loguru based on the `PALITRA_ENV` environment variable:

- **Development** (default): Console output with colors, DEBUG level
- **Production**: File output with rotation, WARNING level

### Usage

```python
from palitra.utils import logger, PalitraError, DeadlockError, RunnerError

# Logging
logger.info("Starting operation")
logger.error("Something went wrong")

# Exceptions
try:
    # Some operation
    pass
except DeadlockError as e:
    logger.error(f"Deadlock detected: {e}")
except RunnerError as e:
    logger.error(f"Runner error: {e}")
```

## Environment Configuration

Set `PALITRA_ENV=production` to enable production logging mode. 